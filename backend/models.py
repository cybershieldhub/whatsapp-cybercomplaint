import uuid
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum

Base = declarative_base()

# Session states
class SessionState(Enum):
    START = "START"
    COLLECTING = "COLLECTING"
    PREFILL_REQUESTED = "PREFILL_REQUESTED"
    AWAITING_CAPTCHA = "AWAITING_CAPTCHA"
    AWAITING_OTP = "AWAITING_OTP"
    SUBMITTING = "SUBMITTING"
    SUBMITTED = "SUBMITTED"
    EXPIRED = "EXPIRED"

# Session table
class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    phone = Column(String, nullable=False)
    stage = Column(String, default=SessionState.START.value)
    data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if "stage" not in kwargs or kwargs["stage"] is None:
            self.stage = SessionState.START.value
        if "data" not in kwargs or kwargs["data"] is None:
            self.data = {}

    def set_stage(self, new_stage: SessionState):
        self.stage = new_stage.value
