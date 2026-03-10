# 🏁 DevRace

DevRace is a gamified developer quiz platform designed to test coding knowledge across various tech stacks while allowing users to climb competitive ranks from Novice to Legend. 

Currently functioning as a robust local Minimum Viable Product (MVP) with both CLI and GUI interfaces, DevRace is actively preparing for a transition to a mobile-first architecture (React Native + FastAPI).

## ✨ Key Features

* **Secure Authentication:** User passwords are encrypted locally using industry-standard `bcrypt` hashing.
* **Gamified Progression System:** Earn XP for correct answers, build your Legacy XP, and rank up through divisions (Novice, Apprentice, Skilled, Pro, Legend).
* **Dynamic Topic Filtering:** Customize your feed. The database dynamically pulls questions only from your subscribed topics (e.g., Python, React Native, SQL).
* **Asynchronous Quiz Engine:** Features a strict 15-second countdown timer per question to prevent cheating and increase engagement.
* **Smart Memory:** A `user_answers` logging system ensures you never see the exact same question twice until a season reset.
* **Dual Interfaces:** Play via the beautifully stylized Terminal (built with `rich` and `questionary`) or the modern Desktop GUI (built with `tkinter`).

## 🛠️ Current Tech Stack (Local MVP)

* **Language:** Python 3.12.10
* **Database:** SQLite3 (Local `drdb.db`)
* **Security:** `bcrypt`
* **CLI UI:** `questionary`, `rich`, `asyncio`
* **GUI UI:** `tkinter`, `ttk`

## 🚀 Getting Started

### Prerequisites
Ensure you have Python 3 installed. Clone the repository and install the required libraries

```bash
pip install -r requirements.txt
```
### 1. Database Setup & Seeding
Before running the app, you must initialize the database and seed it with the default topics and questions.

```bash
python server/setup.py
```
*(Note: If you are doing a fresh install or changed the schema, delete your existing server/drdb.db file before running this command).*

### 2. Run the Application
You can choose to play DevRace via the terminal or the graphical interface:

For the Terminal CLI:

```bash
python client.py
```

For the Desktop GUI:
```bash
python gui.py
```

## 🗺️ Project Roadmap
DevRace is evolving from a local Python application into a fully-fledged mobile platform.

- [x] Phase 1: Core Engine & Local MVP (SQLite, Gamification, CLI/GUI)
- [ ] Phase 2: API Decoupling (Wrapping the backend in FastAPI)
- [ ] Phase 3: Cloud Migration (Transitioning from SQLite to PostgreSQL via Neon/Supabase)
- [ ] Phase 4: Mobile Client (Building the iOS/Android app using React Native)