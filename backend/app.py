# backend/app.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import os
import uuid
from datetime import datetime

from . import models, db

app = FastAPI()

# Dependency to get DB session
def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


@app.post("/sessions")
def create_session(phone: str = "whatsapp:+911234567890", db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())
    session_entry = models.Session(
        id=session_id,
        phone=phone,
        stage="START",
        created_at=datetime.utcnow()
    )
    db.add(session_entry)
    db.commit()
    db.refresh(session_entry)
    return {"id": session_entry.id, "phone": session_entry.phone, "stage": session_entry.stage}


@app.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(models.Session).all()
    return sessions


@app.post("/evidence/{session_id}/upload")
async def upload_evidence_file(
    session_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Check if session exists
    session_entry = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session_entry:
        raise HTTPException(status_code=404, detail="Session not found")

    # Ensure upload folder exists
    upload_dir = "evidence_files"
    os.makedirs(upload_dir, exist_ok=True)

    saved_path = os.path.join(upload_dir, file.filename)

    # Save the file
    try:
        with open(saved_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Create Evidence entry
    evidence_entry = models.Evidence(
        complaint_id=session_id,
        file_path=saved_path,
        created_at=datetime.utcnow()
    )
    db.add(evidence_entry)
    db.commit()
    db.refresh(evidence_entry)

    return {"id": evidence_entry.id, "file_path": evidence_entry.file_path}
