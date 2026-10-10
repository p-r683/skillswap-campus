"""
API router: /api/chat/*  (HTTP REST + WebSocket)
  GET  /api/chat/sessions           — all my chat sessions
  GET  /api/chat/sessions/{id}      — session detail + messages
  POST /api/chat/sessions/{id}/link — mentor sets a Meet/Zoom link
  WS   /api/chat/ws/{session_id}?token=JWT  — real-time messaging
"""
import json, datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import User, ChatSession, ChatMessage, ExchangeRequest
from ..auth import get_current_user, decode_token
from ..ws_manager import manager

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _serialize_message(m: ChatMessage) -> dict:
    return {
        "id": m.id,
        "session_id": m.session_id,
        "sender_id": m.sender_id,
        "sender_name": m.sender.name,
        "sender_initials": m.sender.avatar_initials,
        "sender_color": m.sender.avatar_color,
        "content": m.content,
        "msg_type": m.msg_type,
        "created_at": m.created_at.strftime("%H:%M"),
        "date": m.created_at.strftime("%d %b %Y"),
    }


def _serialize_session(s: ChatSession, current_user_id: int) -> dict:
    peer = s.learner if s.mentor_id == current_user_id else s.mentor
    return {
        "id": s.id,
        "skill_name": s.skill_name,
        "status": s.status,
        "session_link": s.session_link,
        "created_at": s.created_at.strftime("%d %b %Y"),
        "mentor_id": s.mentor_id,
        "learner_id": s.learner_id,
        "mentor_name": s.mentor.name,
        "learner_name": s.learner.name,
        "peer_id": peer.id,
        "peer_name": peer.name,
        "peer_initials": peer.avatar_initials,
        "peer_color": peer.avatar_color,
        "is_mentor": s.mentor_id == current_user_id,
        "request_id": s.request_id,
        "last_message": _serialize_message(s.messages[-1]) if s.messages else None,
        "unread_count": 0,  # simplified — can be enhanced with read receipts
    }


# ─── REST ROUTES ──────────────────────────────────────────────
@router.get("/sessions")
def list_my_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(
        (ChatSession.mentor_id == current_user.id) |
        (ChatSession.learner_id == current_user.id)
    ).order_by(ChatSession.created_at.desc()).all()
    return [_serialize_session(s, current_user.id) for s in sessions]


@router.get("/sessions/{session_id}")
def get_session(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found.")
    if current_user.id not in (s.mentor_id, s.learner_id):
        raise HTTPException(status_code=403, detail="Access denied.")
    result = _serialize_session(s, current_user.id)
    result["messages"] = [_serialize_message(m) for m in s.messages]
    return result


class SetLink(BaseModel):
    link: str


@router.post("/sessions/{session_id}/link")
def set_session_link(
    session_id: int, payload: SetLink,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    s = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found.")
    if s.mentor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the mentor can set the session link.")

    s.session_link = payload.link
    # Post system message with link
    msg = ChatMessage(
        session_id=s.id, sender_id=current_user.id,
        content=f"🔗 Mentor shared the session link: {payload.link}",
        msg_type="link"
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {"message": "Session link set.", "link": payload.link}


# ─── WEBSOCKET ────────────────────────────────────────────────
@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    # Authenticate via query-param token (browsers can't set WS headers)
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001)
        return

    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=4001)
        return

    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session or user_id not in (session.mentor_id, session.learner_id):
        await websocket.close(code=4003)
        return

    await manager.connect(websocket, session_id, user_id)

    # Notify others someone joined
    await manager.broadcast(session_id, {
        "event": "user_joined",
        "user_id": user_id,
        "user_name": user.name,
    })

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            content = data.get("content", "").strip()
            if not content:
                continue

            # Persist message
            msg = ChatMessage(
                session_id=session_id,
                sender_id=user_id,
                content=content,
                msg_type=data.get("msg_type", "text"),
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)

            # Broadcast to the room
            await manager.broadcast(session_id, {
                "event": "message",
                **_serialize_message(msg),
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        await manager.broadcast(session_id, {
            "event": "user_left",
            "user_id": user_id,
            "user_name": user.name,
        })
