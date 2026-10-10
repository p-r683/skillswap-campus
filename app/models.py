import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    avatar_initials = Column(String, default="SS")         # fallback initials if no avatar
    avatar_color = Column(String, default="#0284c7")       # personalized avatar color
    bio = Column(Text, nullable=True)
    college = Column(String, default="AKTU University Campus")
    department = Column(String, nullable=False)
    year = Column(String, nullable=False)                  # e.g. "3rd Year"
    credit_balance = Column(Integer, default=50)           # 50 credit welcome bonus
    rating_score = Column(Float, default=5.0)
    rating_count = Column(Integer, default=0)
    badges_json = Column(Text, default='["🚀 Early Adopter", "🎓 Verified Student"]')
    is_verified = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    sent_requests = relationship(
        "ExchangeRequest", foreign_keys="ExchangeRequest.sender_id", back_populates="sender"
    )
    received_requests = relationship(
        "ExchangeRequest", foreign_keys="ExchangeRequest.receiver_id", back_populates="receiver"
    )
    credit_ledger = relationship("CreditTransaction", back_populates="user")
    sent_messages = relationship(
        "ChatMessage", foreign_keys="ChatMessage.sender_id", back_populates="sender"
    )


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, nullable=False)
    icon = Column(String, default="code")


class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    skill_type = Column(String, nullable=False)            # "teach" or "learn"
    proficiency = Column(String, default="Intermediate")
    credit_rate = Column(Integer, default=10)
    peer_verified = Column(Boolean, default=True)
    endorsement_count = Column(Integer, default=3)

    user = relationship("User", back_populates="skills")
    skill = relationship("Skill")


class ExchangeRequest(Base):
    __tablename__ = "exchange_requests"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    hours = Column(Float, default=1.0)
    total_credits = Column(Integer, default=10)
    note = Column(Text, nullable=True)
    status = Column(String, default="pending")             # pending, accepted, completed, declined, cancelled
    scheduled_at = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_requests")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_requests")
    skill = relationship("Skill")
    # Each accepted request gets one chat session
    chat_session = relationship("ChatSession", back_populates="request", uselist=False)


class ChatSession(Base):
    """Created when an ExchangeRequest is accepted. Ties to a chat room."""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("exchange_requests.id"), unique=True, nullable=False)
    mentor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    learner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    status = Column(String, default="active")              # active, completed
    session_link = Column(String, nullable=True)           # Google Meet / Zoom link
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    request = relationship("ExchangeRequest", back_populates="chat_session")
    mentor = relationship("User", foreign_keys=[mentor_id])
    learner = relationship("User", foreign_keys=[learner_id])
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    msg_type = Column(String, default="text")              # text, system, link, file
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("exchange_requests.id"), nullable=False)
    mentor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    learner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, default=5)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    transaction_type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="credit_ledger")


class ProjectPost(Base):
    __tablename__ = "project_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    college = Column(String, default="AKTU University Campus")
    required_skills_json = Column(Text, default='[]')
    status = Column(String, default="open")
    applicants_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    creator = relationship("User")
