# backend/scripts/create_session.py
from backend.db import SessionLocal
from backend.models import Session
from uuid import uuid4

db = SessionLocal()
s = Session(id=str(uuid4()), phone="whatsapp:+911234567890", stage="START", data={})
db.add(s)
db.commit()
print("Created test session ID:", s.id)
db.close()
