from db import Base, engine
from models import User, Session, Complaint, EvidenceFile

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
