"""
API router: /api/users/*
  GET /api/users               — list all peers (authenticated)
  GET /api/users/{id}          — public profile
  PATCH /api/users/me/skills   — update logged-in user's skills
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import User, Skill, UserSkill
from ..auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


def _serialize_user(u: User, include_ledger=False):
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
    data = {
        "id": u.id, "name": u.name, "email": u.email,
        "avatar_initials": u.avatar_initials, "avatar_color": u.avatar_color,
        "bio": u.bio, "college": u.college, "department": u.department,
        "year": u.year, "credit_balance": u.credit_balance,
        "rating_score": u.rating_score, "rating_count": u.rating_count,
        "badges": json.loads(u.badges_json) if u.badges_json else [],
        "is_verified": u.is_verified, "is_online": u.is_online,
        "teach_skills": teach_skills, "learn_skills": learn_skills,
    }
    if include_ledger:
        data["credit_ledger"] = [
            {"id": t.id, "amount": t.amount, "type": t.transaction_type,
             "description": t.description, "date": t.created_at.strftime("%d %b %Y %H:%M")}
            for t in u.credit_ledger
        ]
    return data


@router.get("")
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [_serialize_user(u) for u in users]


@router.get("/me/full")
def get_my_full_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _serialize_user(current_user, include_ledger=True)


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return _serialize_user(u, include_ledger=True)


class SkillUpdate(BaseModel):
    teach_skills: Optional[List[str]] = None
    learn_skills: Optional[List[str]] = None


@router.patch("/me/skills")
def update_my_skills(
    payload: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Remove existing and re-add
    if payload.teach_skills is not None:
        db.query(UserSkill).filter(
            UserSkill.user_id == current_user.id,
            UserSkill.skill_type == "teach"
        ).delete()
        for sname in payload.teach_skills:
            skill = db.query(Skill).filter(Skill.name == sname).first()
            if skill:
                db.add(UserSkill(user_id=current_user.id, skill_id=skill.id,
                                 skill_type="teach", proficiency="Intermediate", credit_rate=10))

    if payload.learn_skills is not None:
        db.query(UserSkill).filter(
            UserSkill.user_id == current_user.id,
            UserSkill.skill_type == "learn"
        ).delete()
        for sname in payload.learn_skills:
            skill = db.query(Skill).filter(Skill.name == sname).first()
            if skill:
                db.add(UserSkill(user_id=current_user.id, skill_id=skill.id,
                                 skill_type="learn", proficiency="Beginner", credit_rate=10))

    db.commit()
    return {"message": "Skills updated successfully"}
