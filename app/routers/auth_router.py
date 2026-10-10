"""
API router: /api/auth/*
  POST /api/auth/register
  POST /api/auth/login
  GET  /api/auth/me
"""
import json, random
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import User, Skill, UserSkill, CreditTransaction
from ..auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, AVATAR_COLORS
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

DEPARTMENTS = [
    "Computer Science & Engineering",
    "Artificial Intelligence & Data Science",
    "Electronics & Communication",
    "Mechanical Engineering",
    "Design & Media Arts",
    "School of Management",
    "Civil Engineering",
    "Information Technology",
]

YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year"]


# ─── SCHEMAS ─────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    department: str
    year: str
    college: Optional[str] = "AKTU University Campus"
    bio: Optional[str] = None
    teach_skills: Optional[List[str]] = []
    learn_skills: Optional[List[str]] = []


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    name: str


# ─── ROUTES ──────────────────────────────────────────────────
@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")

    initials = "".join(w[0].upper() for w in payload.name.split()[:2])
    color = random.choice(AVATAR_COLORS)

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        avatar_initials=initials,
        avatar_color=color,
        bio=payload.bio or f"{payload.year} student at {payload.college}.",
        college=payload.college,
        department=payload.department,
        year=payload.year,
        credit_balance=50,  # 50-credit welcome gift
        badges_json='["🚀 Early Adopter", "🎓 Verified Student"]',
    )
    db.add(user)
    db.flush()

    # Attach skills
    for skill_name in payload.teach_skills:
        skill = db.query(Skill).filter(Skill.name == skill_name).first()
        if skill:
            db.add(UserSkill(user_id=user.id, skill_id=skill.id, skill_type="teach",
                             proficiency="Intermediate", credit_rate=10))

    for skill_name in payload.learn_skills:
        skill = db.query(Skill).filter(Skill.name == skill_name).first()
        if skill:
            db.add(UserSkill(user_id=user.id, skill_id=skill.id, skill_type="learn",
                             proficiency="Beginner", credit_rate=10))

    # Welcome bonus credit transaction
    db.add(CreditTransaction(
        user_id=user.id, amount=50,
        transaction_type="signup_bonus",
        description="Welcome gift — 50 Skill Credits on joining SkillSwap Campus"
    ))

    db.commit()
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer",
            "user_id": user.id, "name": user.name}


@router.post("/login")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer",
            "user_id": user.id, "name": user.name}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    u = current_user
    teach_skills = [
        {"id": us.skill.id, "name": us.skill.name, "category": us.skill.category,
         "proficiency": us.proficiency, "rate": us.credit_rate}
        for us in u.skills if us.skill_type == "teach"
    ]
    learn_skills = [
        {"id": us.skill.id, "name": us.skill.name, "category": us.skill.category,
         "proficiency": us.proficiency, "rate": us.credit_rate}
        for us in u.skills if us.skill_type == "learn"
    ]
    ledger = [
        {"id": t.id, "amount": t.amount, "type": t.transaction_type,
         "description": t.description, "date": t.created_at.strftime("%d %b %Y %H:%M")}
        for t in u.credit_ledger
    ]
    return {
        "id": u.id, "name": u.name, "email": u.email,
        "avatar_initials": u.avatar_initials, "avatar_color": u.avatar_color,
        "bio": u.bio, "college": u.college, "department": u.department,
        "year": u.year, "credit_balance": u.credit_balance,
        "rating_score": u.rating_score, "rating_count": u.rating_count,
        "badges": json.loads(u.badges_json) if u.badges_json else [],
        "is_verified": u.is_verified, "is_online": u.is_online,
        "teach_skills": teach_skills, "learn_skills": learn_skills,
        "credit_ledger": ledger,
    }


@router.get("/departments")
def list_departments():
    return DEPARTMENTS


@router.get("/years")
def list_years():
    return YEARS
