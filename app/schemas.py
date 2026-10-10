from pydantic import BaseModel, EmailStr
from typing import List, Optional

class RequestCreate(BaseModel):
    sender_id: int
    receiver_id: int
    skill_name: str
    hours: float = 1.0
    note: str

class RequestStatusUpdate(BaseModel):
    status: str # accepted, completed, declined, cancelled

class ReviewCreate(BaseModel):
    request_id: int
    mentor_id: int
    learner_id: int
    rating: int
    comment: str

class ProjectCreate(BaseModel):
    creator_id: int
    title: str
    description: str
    required_skills: List[str]

class UserCreate(BaseModel):
    name: str
    email: str
    department: str
    year: str
    teach_skills: List[str]
    learn_skills: List[str]
