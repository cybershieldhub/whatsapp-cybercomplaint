# backend/models.py
from sqlalchemy import Column, Integer, String, DateTime
from .db import Base
from datetime import datetime

# Session table
class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, index=True)
    phone = Column(String)
    stage = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Evidence table
class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
