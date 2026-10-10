"""
WebSocket connection manager for real-time chat sessions.
Each chat session (tied to an accepted ExchangeRequest) gets its own room.
"""
from __future__ import annotations
import json, datetime
from fastapi import WebSocket
from typing import Dict, List


class ConnectionManager:
    def __init__(self):
        # room_id (session_id) -> list of active WebSocket connections
        self._rooms: Dict[int, List[WebSocket]] = {}
        # ws -> user_id mapping
        self._ws_user: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, session_id: int, user_id: int):
        await websocket.accept()
        self._rooms.setdefault(session_id, []).append(websocket)
        self._ws_user[websocket] = user_id

    def disconnect(self, websocket: WebSocket, session_id: int):
        self._rooms.get(session_id, [])
        if session_id in self._rooms:
            self._rooms[session_id] = [
                ws for ws in self._rooms[session_id] if ws is not websocket
            ]
        self._ws_user.pop(websocket, None)

    async def broadcast(self, session_id: int, payload: dict):
        """Send JSON payload to every connection in the session room."""
        dead = []
        for ws in self._rooms.get(session_id, []):
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, session_id)

    def room_user_count(self, session_id: int) -> int:
        return len(self._rooms.get(session_id, []))


manager = ConnectionManager()
