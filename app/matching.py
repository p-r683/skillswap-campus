import json
from sqlalchemy.orm import Session
from .models import User, UserSkill, Skill

def calculate_skill_match_score(user_a: User, user_b: User, db: Session):
    """
    Calculates mutual skill swap suitability score between user_a and user_b:
    1. Direct Swap Score: Does user_a teach what user_b wants to learn, AND user_b teach what user_a wants to learn? (High Priority 2-way Loop)
    2. One-way Mentorship: Does user_b teach skills user_a wants to learn?
    3. Rating & Endorsement bonus.
    """
    if user_a.id == user_b.id:
        return 0, [], "Self"

    a_teach = {us.skill.name for us in user_a.skills if us.skill_type == "teach"}
    a_learn = {us.skill.name for us in user_a.skills if us.skill_type == "learn"}

    b_teach = {us.skill.name for us in user_b.skills if us.skill_type == "teach"}
    b_learn = {us.skill.name for us in user_b.skills if us.skill_type == "learn"}

    # Direct 2-Way Skill Swap Loop
    a_can_teach_b = a_teach.intersection(b_learn)
    b_can_teach_a = b_teach.intersection(a_learn)

    score = 0
    match_reasons = []
    match_type = "Standard Mentor"

    if a_can_teach_b and b_can_teach_a:
        score += 65
        match_type = "🔄 Perfect 2-Way Swap!"
        match_reasons.append(f"Direct Swap: You teach {', '.join(a_can_teach_b)} & {user_b.name} teaches {', '.join(b_can_teach_a)}")
    elif b_can_teach_a:
        score += 40
        match_type = "👨‍🏫 Mentor Match"
        match_reasons.append(f"{user_b.name} can mentor you in: {', '.join(b_can_teach_a)}")

    # Department affinity
    if user_a.department == user_b.department:
        score += 10
        match_reasons.append(f"Same Department ({user_a.department})")

    # High Rating Bonus
    if user_b.rating_score >= 4.8:
        score += 15
        match_reasons.append(f"Top Rated Mentor ({user_b.rating_score}⭐)")

    # Cap score at 99%
    final_score = min(99, max(25, score)) if match_reasons else 0

    return final_score, match_reasons, match_type

def get_ai_recommendations(user_id: int, db: Session):
    current_user = db.query(User).filter(User.id == user_id).first()
    if not current_user:
        return []

    all_users = db.query(User).filter(User.id != user_id).all()
    recommendations = []

    for peer in all_users:
        score, reasons, match_type = calculate_skill_match_score(current_user, peer, db)
        if score > 0:
            peer_teach_skills = [us.skill.name for us in peer.skills if us.skill_type == "teach"]
            peer_learn_skills = [us.skill.name for us in peer.skills if us.skill_type == "learn"]

            recommendations.append({
                "peer_id": peer.id,
                "peer_name": peer.name,
                "peer_initials": peer.avatar_initials,
                "peer_color": peer.avatar_color,
                "peer_department": peer.department,
                "peer_year": peer.year,
                "rating_score": peer.rating_score,
                "credit_rate": 10,
                "match_score": score,
                "match_type": match_type,
                "match_reasons": reasons,
                "teach_skills": peer_teach_skills,
                "learn_skills": peer_learn_skills
            })

    # Sort by highest match score
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    return recommendations
