# backend/models.py
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Integer, JSON, Text
from .db import Base

# Session state enum
class SessionState(str, Enum):
    START = "START"
    COLLECTING = "COLLECTING"
    PREFILL_REQUESTED = "PREFILL_REQUESTED"
    AWAITING_CAPTCHA = "AWAITING_CAPTCHA"
    AWAITING_OTP = "AWAITING_OTP"
    SUBMITTING = "SUBMITTING"
    SUBMITTED = "SUBMITTED"
    EXPIRED = "EXPIRED"


class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    phone = Column(String, nullable=False, index=True)
    stage = Column(String, nullable=False, default=SessionState.START.value)
    data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    def __init__(self, **kwargs):
        # ensure defaults available when creating object in Python (not yet persisted)
        super().__init__(**kwargs)
        if "stage" not in kwargs or kwargs.get("stage") is None:
            self.stage = SessionState.START.value
        if "data" not in kwargs or kwargs.get("data") is None:
            self.data = {}

    def set_stage(self, new_stage: SessionState):
        self.stage = new_stage.value


class EvidenceFile(Base):
    __tablename__ = "evidence_files"
    # use integer id for simplicity in local dev
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    complaint_id = Column(String, nullable=False, index=True)  # linked to session.id for now
    file_path = Column(String, nullable=False)                 # saved path like /uploads/xxx.jpg or evidence_files/xxx
    original_filename = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
