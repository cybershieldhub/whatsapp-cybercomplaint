from pydantic import BaseModel

class ComplaintBase(BaseModel):
    name: str
    email: str
    details: str

class ComplaintCreate(ComplaintBase):
    pass

class Complaint(ComplaintBase):
    id: int

    class Config:
        orm_mode = True
