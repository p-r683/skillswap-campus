"""
SkillSwap Campus — Main FastAPI Application (Production)
JWT Auth | Real-time WebSocket Chat | Escrow Credits
"""
import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from .database import init_db, SessionLocal
from .models import User
from .seed import seed_data

from .routers.auth_router import router as auth_router
from .routers.users_router import router as users_router
from .routers.requests_router import router as requests_router
from .routers.chat_router import router as chat_router
from .routers.other_routers import (
    skills_router, matching_router, projects_router,
    leaderboard_router, admin_router,
)

app = FastAPI(
    title="SkillSwap Campus API",
    version="2.0.0",
    description="Peer-to-peer skill exchange platform for university students.",
)

# ── CORS (allow all for dev; restrict to your domain in prod) ─
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── STARTUP ────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()
    db = SessionLocal()
    if db.query(User).count() == 0:
        print("No users found — running seed...")
        seed_data()
    db.close()


# ── ROUTERS ───────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(requests_router)
app.include_router(chat_router)
app.include_router(skills_router)
app.include_router(matching_router)
app.include_router(projects_router)
app.include_router(leaderboard_router)
app.include_router(admin_router)


# ── STATIC FRONTEND ───────────────────────────────────────────
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/{path:path}", response_class=HTMLResponse, include_in_schema=False)
def spa(path: str = ""):
    index = os.path.join(static_dir, "index.html")
    if os.path.isfile(index):
        return HTMLResponse(open(index, encoding="utf-8").read())
    return HTMLResponse("<h1>SkillSwap Campus API — v2.0</h1>")
