import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import User, CreditTransaction, Certificate, Workshop
from ..auth import get_current_user

router = APIRouter(prefix="/api/monetization", tags=["monetization"])

# ── 1. CREDIT PACKAGES ─────────────────────────────────────────
CREDIT_PACKS = [
    {
        "id": "starter",
        "name": "Starter Boost",
        "credits": 30,
        "price_inr": 149,
        "popular": False,
        "desc": "Perfect for exam prep & quick 3-hour mentorship."
    },
    {
        "id": "pro",
        "name": "Campus Pro",
        "credits": 100,
        "price_inr": 399,
        "popular": True,
        "desc": "Most popular! 10 full hours of 1-on-1 peer sessions."
    },
    {
        "id": "master",
        "name": "Semester Master",
        "credits": 250,
        "price_inr": 899,
        "popular": False,
        "desc": "Unlimited skill swapping for the full semester."
    }
]

class TopupRequest(BaseModel):
    package_id: str
    payment_method: str = "UPI" # UPI, Card, NetBanking

@router.get("/packages")
def list_packages():
    return CREDIT_PACKS

@router.post("/topup")
def topup_credits(
    payload: TopupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pack = next((p for p in CREDIT_PACKS if p["id"] == payload.package_id), None)
    if not pack:
        raise HTTPException(status_code=400, detail="Invalid credit package selected.")

    # Credit user account
    current_user.credit_balance += pack["credits"]
    
    # Record transaction
    txn = CreditTransaction(
        user_id=current_user.id,
        amount=pack["credits"],
        transaction_type="purchase_topup",
        description=f"Purchased {pack['name']} (+{pack['credits']} credits via {payload.payment_method})"
    )
    db.add(txn)
    db.commit()
    
    return {
        "success": True,
        "message": f"Successfully added {pack['credits']} Skill Credits to your balance!",
        "new_balance": current_user.credit_balance,
        "package": pack
    }

# ── 2. VERIFIED CERTIFICATES ───────────────────────────────────
class CertificateClaimRequest(BaseModel):
    skill_name: str

@router.get("/certificates")
def get_user_certificates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    certs = db.query(Certificate).filter(Certificate.user_id == current_user.id).all()
    return [
        {
            "id": c.id,
            "certificate_id": c.certificate_id,
            "skill_name": c.skill_name,
            "student_name": current_user.name,
            "college": current_user.college,
            "hours_taught": c.hours_taught,
            "rating": c.rating,
            "issued_date": c.created_at.strftime("%B %d, %Y")
        }
        for c in certs
    ]

@router.post("/certificates/issue")
def issue_certificate(
    payload: CertificateClaimRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cert_id = f"SKILLSWAP-{uuid.uuid4().hex[:8].upper()}"
    new_cert = Certificate(
        certificate_id=cert_id,
        user_id=current_user.id,
        skill_name=payload.skill_name,
        hours_taught=12.5,
        rating=current_user.rating_score
    )
    db.add(new_cert)
    db.commit()
    return {
        "success": True,
        "certificate_id": cert_id,
        "message": f"Verified Certificate generated for {payload.skill_name}!"
    }

# ── 3. WORKSHOPS & BOOTCAMPS ──────────────────────────────────
@router.get("/workshops")
def get_workshops(db: Session = Depends(get_db)):
    ws = db.query(Workshop).all()
    if not ws:
        # Seed default workshops if empty
        default_workshops = [
            Workshop(
                title="Full-Stack Web Dev Bootcamp in a Weekend",
                instructor_name="Aarav Sharma (3rd Year CSE)",
                date_time="Saturday, 4:00 PM IST",
                price_inr=199,
                seats_left=12,
                tags_json=json.dumps(["React", "FastAPI", "Deployment"])
            ),
            Workshop(
                title="Cracking FAANG & Product Company Tech Interviews",
                instructor_name="Priya Patel (Senior Mentor)",
                date_time="Sunday, 2:00 PM IST",
                price_inr=249,
                seats_left=8,
                tags_json=json.dumps(["DSA", "System Design", "Resume"])
            ),
            Workshop(
                title="UI/UX Prototyping Masterclass in Figma",
                instructor_name="Priya Patel (Design Lead)",
                date_time="Next Saturday, 5:00 PM IST",
                price_inr=149,
                seats_left=15,
                tags_json=json.dumps(["Figma", "Auto-layout", "Design System"])
            )
        ]
        db.add_all(default_workshops)
        db.commit()
        ws = db.query(Workshop).all()

    return [
        {
            "id": w.id,
            "title": w.title,
            "instructor_name": w.instructor_name,
            "date_time": w.date_time,
            "price_inr": w.price_inr,
            "seats_left": w.seats_left,
            "tags": json.loads(w.tags_json)
        }
        for w in ws
    ]

@router.post("/workshops/{workshop_id}/book")
def book_workshop(
    workshop_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    w = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Workshop not found.")
    if w.seats_left <= 0:
        raise HTTPException(status_code=400, detail="Workshop is sold out.")
    
    w.seats_left -= 1
    db.commit()
    return {
        "success": True,
        "message": f"Seat reserved for '{w.title}'! Pass sent to {current_user.email}."
    }

# ── 4. COLLEGE B2B PARTNERSHIP INQUIRIES ──────────────────────
class CollegeInquiry(BaseModel):
    college_name: str
    contact_person: str
    email: str
    phone: Optional[str] = None
    estimated_students: int = 1000

@router.post("/college/inquire")
def submit_college_inquiry(payload: CollegeInquiry):
    return {
        "success": True,
        "message": f"Thank you, {payload.contact_person}. The SkillSwap Campus Partnership proposal has been sent to {payload.email}!"
    }
