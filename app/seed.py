"""
Fresh seed with hashed passwords so users can actually log in.
Demo credentials (email / password):
  aarav.sharma@aktu.edu.in   / Demo@1234
  priya.patel@aktu.edu.in    / Demo@1234
  rohan.verma@aktu.edu.in    / Demo@1234
  ananya.sen@aktu.edu.in     / Demo@1234
  devansh.gupta@aktu.edu.in  / Demo@1234
"""
import json
from .database import SessionLocal, engine
from .models import Base, User, Skill, UserSkill, ExchangeRequest, CreditTransaction, ProjectPost
from .auth import hash_password


def seed_data():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # ── SKILLS ────────────────────────────────────────────────
    skills_data = [
        ("Python & Backend", "Technical", "code"),
        ("React & Frontend", "Technical", "layout"),
        ("Figma UI/UX Design", "Design", "palette"),
        ("Machine Learning & AI", "Technical", "cpu"),
        ("Public Speaking & Pitching", "Business", "mic"),
        ("Video Editing & Motion", "Creative", "video"),
        ("Data Structures & Algorithms", "Academic", "git-branch"),
        ("French Conversation", "Language", "globe"),
        ("Financial Modeling", "Business", "trending-up"),
        ("Guitar & Music Theory", "Creative", "music"),
        ("IoT & Robotics", "Technical", "bot"),
        ("Content Strategy & SEO", "Marketing", "edit"),
        ("Flutter & Mobile Dev", "Technical", "smartphone"),
        ("DevOps & Cloud (AWS)", "Technical", "cloud"),
        ("Graphic Design (Illustrator)", "Design", "pen-tool"),
    ]
    skill_objs: dict[str, Skill] = {}
    for name, cat, icon in skills_data:
        s = Skill(name=name, category=cat, icon=icon)
        db.add(s)
        db.flush()
        skill_objs[name] = s

    DEFAULT_PW = hash_password("Demo@1234")

    COLORS = ["#0284c7", "#7c3aed", "#059669", "#d97706", "#dc2626"]

    # ── USERS ─────────────────────────────────────────────────
    users_raw = [
        {
            "name": "Aarav Sharma", "email": "aarav.sharma@aktu.edu.in",
            "initials": "AS", "color": COLORS[0],
            "bio": "3rd Year CSE. Building web apps with Python & FastAPI. Want to level up Figma design.",
            "dept": "Computer Science & Engineering", "year": "3rd Year",
            "credits": 85, "rating": 4.9, "rating_count": 12,
            "badges": '["⭐ Top Mentor", "🔥 Skill Streak", "🎓 Verified Student"]',
            "teach": [("Python & Backend", "Expert"), ("Data Structures & Algorithms", "Advanced")],
            "learn": [("Figma UI/UX Design", "Beginner"), ("Public Speaking & Pitching", "Intermediate")],
        },
        {
            "name": "Priya Patel", "email": "priya.patel@aktu.edu.in",
            "initials": "PP", "color": COLORS[1],
            "bio": "4th Year Design & Media. UI/UX portfolios, Figma expert. Looking for an ML study buddy!",
            "dept": "Design & Media Arts", "year": "4th Year",
            "credits": 110, "rating": 5.0, "rating_count": 18,
            "badges": '["🎨 Design Guru", "⭐ 5-Star Mentor", "🤝 Community Builder"]',
            "teach": [("Figma UI/UX Design", "Expert"), ("Video Editing & Motion", "Advanced"),
                      ("Graphic Design (Illustrator)", "Expert")],
            "learn": [("Machine Learning & AI", "Beginner"), ("Python & Backend", "Beginner")],
        },
        {
            "name": "Rohan Verma", "email": "rohan.verma@aktu.edu.in",
            "initials": "RV", "color": COLORS[2],
            "bio": "2nd Year AI & DS. Kaggle participant. Trade ML for public speaking help!",
            "dept": "Artificial Intelligence & Data Science", "year": "2nd Year",
            "credits": 40, "rating": 4.8, "rating_count": 8,
            "badges": '["🤖 AI Enthusiast", "🎓 Verified Student"]',
            "teach": [("Machine Learning & AI", "Advanced"), ("Python & Backend", "Intermediate")],
            "learn": [("Public Speaking & Pitching", "Beginner"), ("Guitar & Music Theory", "Beginner")],
        },
        {
            "name": "Ananya Sen", "email": "ananya.sen@aktu.edu.in",
            "initials": "AS", "color": COLORS[3],
            "bio": "3rd Year ECE. IoT & Embedded Systems lover. Want to learn React to display sensor data on dashboards.",
            "dept": "Electronics & Communication", "year": "3rd Year",
            "credits": 60, "rating": 4.7, "rating_count": 6,
            "badges": '["🔌 Hardware Hacker", "🎓 Verified Student"]',
            "teach": [("IoT & Robotics", "Advanced")],
            "learn": [("React & Frontend", "Beginner"), ("Flutter & Mobile Dev", "Beginner")],
        },
        {
            "name": "Devansh Gupta", "email": "devansh.gupta@aktu.edu.in",
            "initials": "DG", "color": COLORS[4],
            "bio": "4th Year MBA. Startup pitch coach. I'll turn your idea into a killer deck in exchange for learning Data Structures!",
            "dept": "School of Management", "year": "4th Year",
            "credits": 95, "rating": 4.95, "rating_count": 15,
            "badges": '["💼 Pitch Master", "🏆 Hackathon Champion", "⭐ 5-Star Mentor"]',
            "teach": [("Public Speaking & Pitching", "Expert"), ("Financial Modeling", "Advanced"),
                      ("Content Strategy & SEO", "Advanced")],
            "learn": [("Data Structures & Algorithms", "Beginner"), ("Figma UI/UX Design", "Beginner")],
        },
    ]

    user_objs: dict[str, User] = {}
    for ud in users_raw:
        u = User(
            name=ud["name"], email=ud["email"],
            hashed_password=DEFAULT_PW,
            avatar_initials=ud["initials"], avatar_color=ud["color"],
            bio=ud["bio"], college="AKTU University Campus",
            department=ud["dept"], year=ud["year"],
            credit_balance=ud["credits"],
            rating_score=ud["rating"], rating_count=ud["rating_count"],
            badges_json=ud["badges"], is_verified=True,
        )
        db.add(u)
        db.flush()
        user_objs[u.name] = u

        for sk_name, prof in ud["teach"]:
            db.add(UserSkill(user_id=u.id, skill_id=skill_objs[sk_name].id,
                             skill_type="teach", proficiency=prof, credit_rate=10,
                             peer_verified=True, endorsement_count=5))
        for sk_name, prof in ud["learn"]:
            db.add(UserSkill(user_id=u.id, skill_id=skill_objs[sk_name].id,
                             skill_type="learn", proficiency=prof, credit_rate=10))

    # ── CREDIT TRANSACTIONS (sample history) ──────────────────
    txns = [
        (user_objs["Aarav Sharma"], 50, "signup_bonus", "Welcome gift — 50 credits"),
        (user_objs["Aarav Sharma"], 35, "session_earn", "Taught Python basics to Ananya (+35)"),
        (user_objs["Priya Patel"], 50, "signup_bonus", "Welcome gift — 50 credits"),
        (user_objs["Priya Patel"], 60, "session_earn", "6 hours of Figma mentoring"),
        (user_objs["Devansh Gupta"], 50, "signup_bonus", "Welcome gift — 50 credits"),
        (user_objs["Devansh Gupta"], 10, "session_earn", "Pitch review with Rohan"),
        (user_objs["Rohan Verma"], 50, "signup_bonus", "Welcome gift — 50 credits"),
        (user_objs["Ananya Sen"], 50, "signup_bonus", "Welcome gift — 50 credits"),
    ]
    for user, amt, ttype, desc in txns:
        db.add(CreditTransaction(user_id=user.id, amount=amt,
                                  transaction_type=ttype, description=desc))

    # ── SAMPLE EXCHANGE REQUESTS ───────────────────────────────
    req1 = ExchangeRequest(
        sender_id=user_objs["Rohan Verma"].id,
        receiver_id=user_objs["Devansh Gupta"].id,
        skill_id=skill_objs["Public Speaking & Pitching"].id,
        hours=1.0, total_credits=10,
        note="Need pitch coaching before Smart India Hackathon next week!",
        status="pending",
    )
    db.add(req1)

    req2 = ExchangeRequest(
        sender_id=user_objs["Ananya Sen"].id,
        receiver_id=user_objs["Aarav Sharma"].id,
        skill_id=skill_objs["Python & Backend"].id,
        hours=1.5, total_credits=15,
        note="I want to learn FastAPI to build a REST API for my IoT sensor dashboard.",
        status="pending",
    )
    db.add(req2)

    # ── SAMPLE PROJECTS ───────────────────────────────────────
    projects = [
        ProjectPost(
            title="Campus AI Eco-Tracker App",
            description="Building an AI-powered waste segregation & carbon footprint tracker for campus sustainability week. Need a Figma designer and a React dev.",
            creator_id=user_objs["Aarav Sharma"].id,
            college="AKTU University Campus",
            required_skills_json=json.dumps(["Figma UI/UX Design", "React & Frontend", "Python & Backend"]),
            status="open", applicants_count=3,
        ),
        ProjectPost(
            title="Smart Hostel IoT Automation",
            description="Open-source IoT system for hostel energy monitoring. Need React dashboard + embedded circuit testing.",
            creator_id=user_objs["Ananya Sen"].id,
            college="AKTU University Campus",
            required_skills_json=json.dumps(["IoT & Robotics", "React & Frontend"]),
            status="open", applicants_count=2,
        ),
    ]
    for p in projects:
        db.add(p)

    db.commit()
    db.close()
    print("Database seeded! Login with any seed user at Demo@1234")


if __name__ == "__main__":
    seed_data()
