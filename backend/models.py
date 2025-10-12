from sqlalchemy import Column, Integer, String
from db import Base

class Complaint(Base):
    __tablename__ = 'complaints'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    details = Column(String)
