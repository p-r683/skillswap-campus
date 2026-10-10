# SkillSwap Campus 🎓

> Peer-to-peer skill exchange platform designed for colleges and universities with AI-assisted match recommendations, hybrid time credits, and live teaching chat rooms.

---

## 🌟 Key Features
- **Student Verification & Auth**: Secure bcrypt-hashed passwords + JWT Bearer token sessions.
- **Skill Marketplace**: Search and filter campus peers teaching technical, design, business, and creative topics.
- **Escrow-Secured Credit Economy**: 1 hour = 10 Skill Credits. Credits are held in escrow when booking sessions and released on completion.
- **Real-Time Teaching Chat**: WebSocket-powered 1-on-1 messaging with video link sharing (Google Meet / Zoom).
- **AI Matching Engine**: Mutual 2-way complementary skill loop calculation.
- **Campus Collaboration Board**: Post hackathon teammate / project partner requests.
- **Leaderboard & Admin Analytics**: Community reputation metrics.

---

## 🚀 Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/<your-username>/skillswap-campus.git
   cd skillswap-campus
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the application**:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Open in browser**:
   Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Demo Credentials
- `aarav.sharma@aktu.edu.in` / `Demo@1234`
- `priya.patel@aktu.edu.in` / `Demo@1234`
- `rohan.verma@aktu.edu.in` / `Demo@1234`
- `ananya.sen@aktu.edu.in` / `Demo@1234`
- `devansh.gupta@aktu.edu.in` / `Demo@1234`
