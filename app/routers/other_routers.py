"""Remaining API routers: skills, matching, projects, leaderboard, admin."""
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    User, Skill, UserSkill, ExchangeRequest, Review, CreditTransaction,
    ProjectPost, ChatSession
)
from ..auth import get_current_user
from ..matching import get_ai_recommendations
from ..seed import seed_data

# ─────────────────────────────────────────────────────────────
skills_router = APIRouter(prefix="/api/skills", tags=["skills"])
matching_router = APIRouter(prefix="/api/matching", tags=["matching"])
projects_router = APIRouter(prefix="/api/projects", tags=["projects"])
leaderboard_router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── SKILLS ────────────────────────────────────────────────────
@skills_router.get("")
def list_skills(db: Session = Depends(get_db)):
    return [{"id": s.id, "name": s.name, "category": s.category, "icon": s.icon}
            for s in db.query(Skill).all()]


# ── MATCHING ──────────────────────────────────────────────────
@matching_router.get("/recommendations")
def recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_ai_recommendations(current_user.id, db)


# ── PROJECTS ──────────────────────────────────────────────────
class ProjectCreate(BaseModel):
    title: str
    description: str
    required_skills: List[str]


@projects_router.get("")
def list_projects(db: Session = Depends(get_db)):
    posts = db.query(ProjectPost).order_by(ProjectPost.created_at.desc()).all()
    return [
        {
            "id": p.id, "title": p.title, "description": p.description,
            "creator_id": p.creator_id, "creator_name": p.creator.name,
            "creator_initials": p.creator.avatar_initials,
            "creator_color": p.creator.avatar_color,
            "department": p.creator.department, "college": p.college,
            "required_skills": json.loads(p.required_skills_json),
            "status": p.status, "applicants_count": p.applicants_count,
            "created_at": p.created_at.strftime("%d %b %Y"),
        }
        for p in posts
    ]


@projects_router.post("", status_code=201)
def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = ProjectPost(
        title=payload.title, description=payload.description,
        creator_id=current_user.id, college=current_user.college,
        required_skills_json=json.dumps(payload.required_skills),
    )
    db.add(p)
    db.commit()
    return {"message": "Project posted!", "project_id": p.id}


# ── LEADERBOARD ───────────────────────────────────────────────
@leaderboard_router.get("")
def leaderboard(db: Session = Depends(get_db)):
    users = db.query(User).order_by(
        User.rating_score.desc(), User.rating_count.desc()
    ).all()
    return [
        {
            "rank": idx + 1,
            "id": u.id, "name": u.name,
            "avatar_initials": u.avatar_initials, "avatar_color": u.avatar_color,
            "department": u.department,
            "credit_balance": u.credit_balance,
            "rating_score": u.rating_score,
            "rating_count": u.rating_count,
            "teach_count": sum(1 for us in u.skills if us.skill_type == "teach"),
            "badges": json.loads(u.badges_json) if u.badges_json else [],
        }
        for idx, u in enumerate(users)
    ]


# ── ADMIN ─────────────────────────────────────────────────────
@admin_router.get("/metrics")
def admin_metrics(db: Session = Depends(get_db)):
    total_students = db.query(User).count()
    total_skills = db.query(Skill).count()
    total_requests = db.query(ExchangeRequest).count()
    completed = db.query(ExchangeRequest).filter(ExchangeRequest.status == "completed").count()
    active_sessions = db.query(ChatSession).filter(ChatSession.status == "active").count()
    total_credits = sum(u.credit_balance for u in db.query(User).all())

    skill_counts: dict = {}
    for us in db.query(UserSkill).filter(UserSkill.skill_type == "learn").all():
        skill_counts[us.skill.name] = skill_counts.get(us.skill.name, 0) + 1
    top5 = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "campus_name": "AKTU University Campus",
        "total_active_students": total_students,
        "total_skills_cataloged": total_skills,
        "total_exchange_requests": total_requests,
        "completed_peer_sessions": completed,
        "active_chat_sessions": active_sessions,
        "total_credits_in_circulation": total_credits,
        "top_in_demand_skills": [{"skill": s, "requests": c} for s, c in top5],
    }


@admin_router.post("/reset")
def reset_db():
    seed_data()
    return {"message": "Database reset to seed state."}
