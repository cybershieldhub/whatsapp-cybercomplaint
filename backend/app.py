# backend/app.py

from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Request
from sqlalchemy.orm import Session
from . import db, models
import os
from uuid import uuid4

# Create upload directory
UPLOAD_DIR = "./evidence_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="WhatsApp Cyber Complaint Backend")

# Dependency
def get_db_session():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

# ----------------------
# Automation Worker
# ----------------------

@app.post("/prefill")
def prefill_session(session_data: dict, db: Session = Depends(get_db_session)):
    """
    Automation worker sends data to prefill a session.
    Example session_data: {"phone": "1234567890", "stage": "start", "data": {...}}
    """
    new_session = models.Session(
        id=str(uuid4()),
        phone=session_data["phone"],
        stage=session_data.get("stage", "start"),
        data=session_data.get("data", {}),
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return {"status": "success", "session_id": new_session.id}


@app.post("/complete/{session_id}")
def complete_session(session_id: str, db: Session = Depends(get_db_session)):
    """
    Mark a session as complete.
    """
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.stage = "completed"
    db.commit()
    return {"status": "success", "session_id": session.id}


# ----------------------
# Evidence Upload
# ----------------------

@app.post("/evidence/{session_id}")
def upload_evidence(session_id: str, file: UploadFile = File(...), db: Session = Depends(get_db_session)):
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    file_path = os.path.join(UPLOAD_DIR, f"{session_id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    
    evidence = models.EvidenceFile(
        complaint_id=session_id,
        file_path=file_path
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    
    return {"status": "success", "file_path": file_path}


# ----------------------
# Admin / Debug Endpoints
# ----------------------

@app.get("/users")
def list_users(db: Session = Depends(get_db_session)):
    return db.query(models.User).all()

@app.get("/sessions")
def list_sessions(db: Session = Depends(get_db_session)):
    return db.query(models.Session).all()

@app.get("/complaints")
def list_complaints(db: Session = Depends(get_db_session)):
    return db.query(models.Complaint).all()


# ----------------------
# Twilio Webhook
# ----------------------

@app.post("/twilio-webhook")
async def twilio_webhook(request: Request, db: Session = Depends(get_db_session)):
    payload = await request.form()
    phone = payload.get("From")
    message = payload.get("Body")
    
    if not phone or not message:
        raise HTTPException(status_code=400, detail="Missing phone or message")
    
    # Find or create session
    session = db.query(models.Session).filter(models.Session.phone == phone).first()
    if not session:
        session = models.Session(id=str(uuid4()), phone=phone, stage="start", data={"messages": []})
        db.add(session)
        db.commit()
        db.refresh(session)
    
    # Append message to session
    if "messages" not in session.data:
        session.data["messages"] = []
    session.data["messages"].append(message)
    db.commit()
    
    return {"status": "received", "phone": phone, "message": message}
