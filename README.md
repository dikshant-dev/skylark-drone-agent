# 🚁 Skylark Drones — Operations Coordinator AI Agent

An AI-powered drone operations coordinator that manages pilot rosters, drone fleets, mission assignments, and detects scheduling conflicts in real time.

---

## 🏗️ Architecture

```
skylark-drones/
├── app.py              # Flask entry point — routes
├── agent.py            # AI brain — handles all messages, OpenAI integration
├── conflicts.py        # Conflict detection engine (deterministic, no LLM)
├── sheets.py           # Google Sheets 2-way sync
├── .env                # API keys (not committed)
├── requirements.txt
├── data/
│   ├── pilot_roster.csv
│   ├── drone_fleet.csv
│   └── missions.csv
└── templates/
    └── index.html      # Chat UI
```

### How it works

```
User Message
    │
    ▼
agent.py (DroneAgent.handle_message)
    │
    ├─► Status Update?  → Update in-memory + Google Sheets sync
    │
    ├─► Conflict Check? → conflicts.py (deterministic Python)
    │       └── check_all_conflicts():
    │               ├── Double-booking detection
    │               ├── Certification mismatch
    │               ├── Skill mismatch
    │               ├── Pilot availability
    │               ├── Budget overrun (rate × days > budget)
    │               ├── Drone in maintenance
    │               ├── Weather risk (Rainy + no IP43)
    │               └── Location mismatch (pilot/drone vs mission)
    │
    ├─► Urgent Reassignment? → Mark unavailable + find replacement
    │
    ├─► Assignment Suggest?  → Match skills/certs + run conflict check
    │
    └─► Freeform Query → OpenAI GPT-3.5-Turbo with full data context
```

---

## ⚡ Features

### Conflict Detection (Unique Selling Point)
| Alert Type | Severity |
|---|---|
| Double-booking (overlapping mission dates) | 🔴 Critical |
| Certification mismatch | 🔴 Critical |
| Drone in maintenance | 🔴 Critical |
| Weather risk (no IP43 in rainy mission) | 🔴 Critical |
| Skill mismatch | 🟡 Warning |
| Budget overrun (pilot cost > mission budget) | 🟡 Warning |
| Location mismatch (pilot/drone vs mission city) | 🟡 Warning |

### Core Features
- ✅ Pilot availability by skill / certification / location
- ✅ Drone matching by weather resistance and capability
- ✅ Assignment suggestions with automatic conflict check
- ✅ Pilot cost calculator (daily rate × mission days)
- ✅ Status updates synced to Google Sheets
- ✅ Urgent reassignment (auto marks pilot unavailable, finds replacement)
- ✅ Conversational AI fallback for any question

---

## 🚀 Setup & Run (Windows)

### 1. Clone / Download the project

```bash
cd Desktop
git clone <your-repo-url>
cd skylark-drones
```

### 2. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure .env

```
OPENAI_API_KEY=your-openai-api-key-here
GOOGLE_SHEET_NAME=Skylark Drones
```

### 5. Google Sheets Setup (optional but required for full marks)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable **Google Sheets API** and **Google Drive API**
3. Create a Service Account → Download `credentials.json`
4. Place `credentials.json` in the project root
5. Create a Google Sheet named **"Skylark Drones"**
6. Add sheets: **"Pilot Roster"** and **"Drone Fleet"**
7. Copy data from CSVs into those sheets
8. Share the Sheet with your service account email (Editor access)

### 6. Run the app

```bash
python app.py
```

Open browser: **http://localhost:5000**

---

## 🌐 Deploy to Railway (Free)

1. Go to [railway.app](https://railway.app) → Sign in with GitHub
2. New Project → Deploy from GitHub repo
3. Add environment variables: `OPENAI_API_KEY` and `GOOGLE_SHEET_NAME`
4. Add `credentials.json` as a file secret
5. Railway auto-detects Flask and deploys ✅

---

## 💬 Example Queries

```
"Show me all available pilots"
"Check conflicts for PRJ001"
"Suggest best assignment for PRJ002"
"Who can fly in rainy weather?"
"Mark Sneha as Available"
"Calculate cost for Arjun on PRJ001"
"Arjun is sick, urgent reassign his mission"
"Which drones are in maintenance?"
"Find a pilot with Night Ops certification in Mumbai"
```

---

## 🔧 Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | Flask (Python) | Simple, familiar, fast to build |
| AI | OpenAI GPT-3.5-Turbo | Cost-effective conversational AI |
| Conflict Engine | Custom Python | Deterministic = no hallucination risk |
| Data | CSV + Pandas | Matches spec; fast for small fleet |
| Sheets Sync | gspread | Official Google Sheets Python library |
| Frontend | HTML/CSS/JS | No build tools, works anywhere |
| Deploy | Railway / Replit | Free, zero-config |

---

## 📄 License

Built for Skylark Drones Technical Assessment.
