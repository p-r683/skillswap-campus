"""
API router: /api/requests/*  (Exchange Requests with escrow credit logic)
  GET  /api/requests           — my requests (sent + received)
  POST /api/requests           — create new request (escrow lock)
  POST /api/requests/{id}/accept   — accept → creates ChatSession
  POST /api/requests/{id}/decline  — decline → refund escrow
  POST /api/requests/{id}/complete — complete → release escrow → open review
"""
import json, datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import (
    User, Skill, ExchangeRequest, ChatSession, ChatMessage, CreditTransaction
)
from ..auth import get_current_user

router = APIRouter(prefix="/api/requests", tags=["requests"])


def _serialize_req(r: ExchangeRequest) -> dict:
    s = r.sender
    rec = r.receiver
    return {
        "id": r.id,
        "sender_id": s.id, "sender_name": s.name,
        "sender_initials": s.avatar_initials, "sender_color": s.avatar_color,
        "receiver_id": rec.id, "receiver_name": rec.name,
        "receiver_initials": rec.avatar_initials, "receiver_color": rec.avatar_color,
        "skill_id": r.skill_id, "skill_name": r.skill.name,
        "hours": r.hours, "total_credits": r.total_credits,
        "note": r.note, "status": r.status,
        "scheduled_at": r.scheduled_at,
        "created_at": r.created_at.strftime("%d %b %Y %H:%M"),
        "chat_session_id": r.chat_session.id if r.chat_session else None,
    }


class CreateRequest(BaseModel):
    receiver_id: int
    skill_name: str
    hours: float = 1.0
    note: str


@router.get("")
def get_my_requests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reqs = db.query(ExchangeRequest).filter(
        (ExchangeRequest.sender_id == current_user.id) |
        (ExchangeRequest.receiver_id == current_user.id)
    ).order_by(ExchangeRequest.created_at.desc()).all()
    return [_serialize_req(r) for r in reqs]


@router.post("", status_code=201)
def create_request(payload: CreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.receiver_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send a request to yourself.")

    receiver = db.query(User).filter(User.id == payload.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found.")

    skill = db.query(Skill).filter(Skill.name == payload.skill_name).first()
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{payload.skill_name}' not found.")

    total_credits = int(payload.hours * 10)
    if current_user.credit_balance < total_credits:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient credits. Need {total_credits}, have {current_user.credit_balance}."
        )

    # Escrow lock
    current_user.credit_balance -= total_credits
    db.add(CreditTransaction(
        user_id=current_user.id, amount=-total_credits,
        transaction_type="escrow_lock",
        description=f"Escrow locked for '{skill.name}' session with {receiver.name}"
    ))

    req = ExchangeRequest(
        sender_id=current_user.id, receiver_id=receiver.id,
        skill_id=skill.id, hours=payload.hours,
        total_credits=total_credits, note=payload.note,
        status="pending"
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return {"message": "Request sent. Credits locked in escrow.", "request_id": req.id}


@router.post("/{request_id}/accept")
def accept_request(request_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    req = db.query(ExchangeRequest).filter(ExchangeRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    if req.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the mentor can accept this request.")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Request is already {req.status}.")

    req.status = "accepted"

    # Create chat session
    session = ChatSession(
        request_id=req.id,
        mentor_id=req.receiver_id,
        learner_id=req.sender_id,
        skill_name=req.skill.name,
        status="active",
    )
    db.add(session)
    db.flush()

    # Post a system welcome message
    db.add(ChatMessage(
        session_id=session.id, sender_id=current_user.id,
        content=f"✅ {current_user.name} accepted the session! This is your private teaching chat for **{req.skill.name}**. You have **{req.hours} hour(s)** booked.",
        msg_type="system"
    ))

    db.commit()
    db.refresh(session)
    return {"message": "Request accepted! Chat session created.", "session_id": session.id}


@router.post("/{request_id}/decline")
def decline_request(request_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    req = db.query(ExchangeRequest).filter(ExchangeRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    if req.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the mentor can decline.")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Request is not in a declinable state.")

    req.status = "declined"
    # Refund escrow to learner
    sender = db.query(User).filter(User.id == req.sender_id).first()
    sender.credit_balance += req.total_credits
    db.add(CreditTransaction(
        user_id=sender.id, amount=req.total_credits,
        transaction_type="escrow_refund",
        description=f"Escrow refunded — session with {current_user.name} declined"
    ))
    db.commit()
    return {"message": "Request declined. Escrow credits refunded to learner."}


class CompleteRequest(BaseModel):
    rating: int = 5
    comment: Optional[str] = ""


@router.post("/{request_id}/complete")
def complete_request(
    request_id: int, payload: CompleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(ExchangeRequest).filter(ExchangeRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found.")
    if req.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the learner can mark as complete.")
    if req.status != "accepted":
        raise HTTPException(status_code=400, detail="Request must be accepted first.")

    req.status = "completed"

    # Release escrow → pay mentor
    mentor = db.query(User).filter(User.id == req.receiver_id).first()
    mentor.credit_balance += req.total_credits
    db.add(CreditTransaction(
        user_id=mentor.id, amount=req.total_credits,
        transaction_type="session_earn",
        description=f"Earned {req.total_credits} credits teaching '{req.skill.name}' to {current_user.name}"
    ))

    # Update mentor rating
    old_total = mentor.rating_score * mentor.rating_count
    mentor.rating_count += 1
    mentor.rating_score = round((old_total + payload.rating) / mentor.rating_count, 2)

    # Close chat session
    if req.chat_session:
        req.chat_session.status = "completed"
        db.add(ChatMessage(
            session_id=req.chat_session.id, sender_id=current_user.id,
            content=f"🎉 Session marked complete by {current_user.name}! {req.total_credits} credits released to mentor. Rating: {'⭐' * payload.rating}",
            msg_type="system"
        ))

    db.commit()
    return {"message": "Session completed! Credits released to mentor."}
