# backend/app.py
import os
from uuid import uuid4
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request, Body
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import httpx

from . import db, models

# Try importing storage helpers; fallback to a minimal local saver
try:
    from .storage import save_bytes_locally, download_url_to_local
except Exception:
    def _safe_filename(name: str) -> str:
        return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".", "_")).strip()

    UPLOAD_DIR = os.getenv("LOCAL_UPLOAD_DIR", "uploads")
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    def save_bytes_locally(filename: str, content: bytes) -> str:
        safe_name = _safe_filename(filename)
        path = os.path.join(UPLOAD_DIR, safe_name)
        with open(path, "wb") as f:
            f.write(content)
        return f"/{UPLOAD_DIR}/{safe_name}"

    def download_url_to_local(url: str, filename_hint: Optional[str] = None, headers: Optional[dict] = None) -> str:
        import requests
        resp = requests.get(url, headers=headers or {}, timeout=30)
        resp.raise_for_status()
        fn = filename_hint or os.path.basename(url.split("?")[0]) or f"file_{uuid4().hex[:8]}"
        return save_bytes_locally(fn, resp.content)

load_dotenv()

UPLOAD_DIR = os.getenv("LOCAL_UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="WhatsApp Cyber Complaint Backend (M1)")

# mount uploads directory so saved files are accessible via /uploads/...
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# -----------------------
# Database dependency
# -----------------------
def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


# -----------------------
# Health check
# -----------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -----------------------
# Sessions endpoints
# -----------------------
@app.post("/sessions")
def create_session(phone: str = "whatsapp:+911234567890", db_session: Session = Depends(get_db)):
    session_id = str(uuid4())
    s = models.Session(id=session_id, phone=phone, stage=models.SessionState.START.value, data={})
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return {"id": s.id, "phone": s.phone, "stage": s.stage}


@app.get("/sessions")
def list_sessions(db_session: Session = Depends(get_db)):
    return db_session.query(models.Session).all()


@app.get("/session/{phone}")
def get_session_by_phone(phone: str, db_session: Session = Depends(get_db)):
    session = (
        db_session.query(models.Session)
        .filter(models.Session.phone == phone)
        .order_by(models.Session.created_at.desc())
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="No session found for that phone")
    if not isinstance(session.data, dict):
        session.data = {}
        db_session.commit()
        db_session.refresh(session)
    return session


# -----------------------
# Evidence listing
# -----------------------
@app.get("/evidence")
def list_evidence(db_session: Session = Depends(get_db)):
    return db_session.query(models.EvidenceFile).all()


# -----------------------
# Upload evidence file
# -----------------------
@app.post("/evidence/{session_id}/upload")
async def upload_evidence_file(
    session_id: str,
    file: UploadFile = File(...),
    db_session: Session = Depends(get_db),
):
    session = db_session.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not isinstance(session.data, dict):
        session.data = {}

    contents = await file.read()
    MAX_BYTES = 12 * 1024 * 1024
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large")

    safe_name = f"{session_id}_{file.filename}"
    saved_path = save_bytes_locally(safe_name, contents)

    ev = models.EvidenceFile(
        complaint_id=session_id,
        file_path=saved_path,
        original_filename=file.filename if hasattr(file, "filename") else None,
        mime_type=getattr(file, "content_type", None),
        size_bytes=len(contents),
    )
    db_session.add(ev)
    db_session.commit()
    db_session.refresh(ev)

    session.data.setdefault("evidence", []).append(saved_path)
    db_session.commit()
    db_session.refresh(session)

    return {"status": "ok", "file_path": saved_path, "evidence_id": ev.id}


# -----------------------
# Twilio-like webhook (form-encoded)
# -----------------------
@app.post("/twilio-webhook")
async def twilio_webhook(request: Request, db_session: Session = Depends(get_db)):
    form = await request.form()
    phone = form.get("From")
    message = form.get("Body")

    if not phone:
        raise HTTPException(status_code=400, detail="Missing From phone number")

    session = (
        db_session.query(models.Session)
        .filter(models.Session.phone == phone)
        .order_by(models.Session.created_at.desc())
        .first()
    )
    if not session:
        session = models.Session(id=str(uuid4()), phone=phone, stage=models.SessionState.START.value, data={})
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

    if not isinstance(session.data, dict):
        session.data = {}

    if message:
        session.data.setdefault("messages", []).append(message)
        db_session.commit()

    saved_urls: List[str] = []
    i = 0
    while True:
        key = f"MediaUrl{i}"
        if key not in form:
            break
        url = form.get(key)
        if not url:
            break
        try:
            saved = download_url_to_local(url)
        except Exception:
            saved = None
        if saved:
            saved_urls.append(saved)
            ev = models.EvidenceFile(complaint_id=session.id, file_path=saved)
            db_session.add(ev)
        i += 1

    if saved_urls:
        db_session.commit()
        session.data.setdefault("evidence", []).extend(saved_urls)
        db_session.commit()

    return {"status": "received", "phone": phone, "message": message, "media_saved": saved_urls}


# -----------------------
# POST /message/{session_id} - simulate an incoming message
# -----------------------
@app.post("/message/{session_id}")
async def post_message(
    session_id: str,
    payload: dict = Body(...),
    db_session: Session = Depends(get_db),
):
    session_id = session_id.strip()
    session = db_session.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        session = models.Session(id=session_id, phone="unknown", stage=models.SessionState.START.value, data={})
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

    if not isinstance(session.data, dict):
        session.data = {}

    msg_text = payload.get("message") if isinstance(payload, dict) else None
    if not msg_text:
        raise HTTPException(status_code=400, detail="Payload must include a 'message' field.")

    session.data.setdefault("messages", []).append({"text": msg_text, "ts": datetime.utcnow().isoformat()})

    if session.stage == models.SessionState.START.value:
        session.set_stage(models.SessionState.COLLECTING)

    db_session.commit()
    db_session.refresh(session)

    return {"status": "ok", "session_id": session.id, "stage": session.stage, "messages": session.data.get("messages")}


# -----------------------
# Integration with automation worker
# -----------------------
SELENIUM_WORKER_URL = os.getenv("SELENIUM_WORKER_URL", "http://localhost:5001")


@app.post("/session/{phone}/prefill")
def prefill_session(phone: str, db_session: Session = Depends(get_db)):
    session = (
        db_session.query(models.Session)
        .filter(models.Session.phone == phone)
        .order_by(models.Session.created_at.desc())
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not isinstance(session.data, dict):
        session.data = {}

    payload = {
        "session_id": session.id,
        "complaint_data": session.data,
        "evidence_urls": session.data.get("evidence", []),
    }

    try:
        with httpx.Client(timeout=15) as client:
            r = client.post(f"{SELENIUM_WORKER_URL}/prefill", json=payload)
            r.raise_for_status()
            resp = r.json()
    except Exception:
        resp = {
            "captcha_url": f"https://example.com/captcha/{session.id}",
            "token": f"mock-token-{session.id[:8]}",
        }

    session.data["captcha_token"] = resp.get("token")
    session.set_stage(models.SessionState.PREFILL_REQUESTED)
    db_session.commit()
    db_session.refresh(session)

    return {"status": "prefill_requested", "captcha_url": resp.get("captcha_url"), "token": resp.get("token")}


# -----------------------
# POST /session/{phone}/complete
# -----------------------
@app.post("/session/{phone}/complete")
def complete_session(phone: str, payload: dict = Body(...), db_session: Session = Depends(get_db)):
    """
    Expect payload: {"captcha_text": "...", "otp": "..."}.
    Calls automation worker /complete with token, captcha_text, otp.
    If worker not reachable, returns mocked response.
    """
    session = (
        db_session.query(models.Session)
        .filter(models.Session.phone == phone)
        .order_by(models.Session.created_at.desc())
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not isinstance(session.data, dict):
        session.data = {}

    token = session.data.get("captcha_token")
    if not token:
        raise HTTPException(status_code=400, detail="No captcha token stored for session")

    captcha_text = payload.get("captcha_text")
    otp = payload.get("otp")

    if not captcha_text:
        raise HTTPException(status_code=400, detail="captcha_text is required")

    body = {"token": token, "captcha_text": captcha_text, "otp": otp}
    try:
        with httpx.Client(timeout=60) as client:
            r = client.post(f"{SELENIUM_WORKER_URL}/complete", json=body)
            r.raise_for_status()
            result = r.json()
    except Exception:
        result = {"status": "submitted", "complaint_id": f"mock-complaint-{session.id[:8]}"}

    if result.get("status") in ("ok", "submitted"):
        session.set_stage(models.SessionState.SUBMITTED)
        session.data.pop("captcha_token", None)
        session.data.pop("otp", None)
        db_session.commit()
        db_session.refresh(session)

    return {"result": result, "session_stage": session.stage}
