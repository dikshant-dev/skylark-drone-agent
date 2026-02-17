Skylark Drones — Operations Coordinator AI Agent

This project is an AI-powered operations coordinator designed for managing drone missions. It helps organize pilot schedules, drone availability, mission assignments, and automatically detects conflicts before they happen.

I built this as part of the Skylark Drones technical assessment to simulate a real-world drone operations system.

🧠 What the System Does

The AI agent acts like an operations manager. It can:

Track pilot availability, skills, and certifications

Manage drone fleet status

Suggest best pilot-drone assignments

Detect scheduling and operational conflicts

Handle urgent reassignment if a pilot becomes unavailable

Sync updates with Google Sheets in real time

Answer operational queries conversationally

⚠️ Conflict Detection (Main Feature)

The system checks for issues before assigning missions:

Critical Alerts

Double-booking of pilots

Certification mismatch

Drone under maintenance

Unsafe weather conditions

Warnings

Skill mismatch

Budget overrun

Location mismatch

This logic is deterministic (pure Python), so results are reliable and not AI-hallucinated.

🏗️ Project Structure
skylark-drones/
├── app.py            # Flask routes
├── agent.py          # AI logic and decision handling
├── conflicts.py      # Conflict detection engine
├── sheets.py         # Google Sheets integration
├── data/             # CSV datasets
├── templates/        # Web interface
└── requirements.txt

⚙️ How It Works

User message → AI agent → decides action:

Status update → updates system + Sheets

Conflict check → runs conflict engine

Assignment request → suggests best match

Urgent issue → auto reassigns

General query → AI response

🚀 Running the Project Locally
1. Clone the repo
git clone <repo-url>
cd skylark-drones

2. Create virtual environment
python -m venv venv
venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Add environment variables

Create .env file:

GROQ_API_KEY=your_api_key
GOOGLE_SHEET_NAME=Skylark Drones

5. Run the app
python app.py


Open:

👉 http://localhost:5000

🌐 Deployment

Deployed using Railway for free hosting.

Steps:

Connect GitHub repo

Add environment variables

Deploy automatically

💬 Example Commands

Try asking:

Show available pilots

Suggest assignment for PRJ001

Check conflicts for mission

Mark pilot as unavailable

Urgent reassignment

🛠️ Tech Stack

Python + Flask

Pandas for data handling

Groq LLM for AI responses

Google Sheets API for sync

HTML/CSS/JS frontend
