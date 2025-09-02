# Daily Check‑In — Flask + SQLite (No JS framework, no Google)

This is a simple website that **just works**:
- Runs locally with Python + SQLite (no external services)
- Deployable to Render or Railway so others can access it
- Data stored in a local `checkins.db` file

## Run locally (Windows-friendly)
1. Install Python 3.11+
2. In this folder:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```
3. Open http://localhost:5000
   - New check-in at `/`
   - Dashboard at `/dashboard`

## Deploy (Render free web service)
1. Create a new GitHub repo and push these files.
2. Go to https://render.com → New → Web Service
3. Select your repo. Build Command: *(leave blank)*, Start Command: `gunicorn app:app`
4. Add environment variables (optional):
   - `APP_NAME=Daily Check-In`
   - `DATABASE_URL=checkins.db` (sqlite file in container; will reset on redeploy)
5. Deploy. You’ll get a public URL.

> NOTE: Free hosts often reset ephemeral disks on redeploy. If you need **durable** cloud storage, swap SQLite for a managed Postgres (Railway/Supabase). I can provide a drop-in `psycopg` version when you’re ready.

## API (optional)
- `GET /api/checkins` — JSON list of last 100 check-ins
- `GET /api/messages` — JSON list of last 100 messages
- `POST /submit` — form post or JSON (`Content-Type: application/json`):
  ```json
  {
    "energy_level": "High",
    "symptom_level": "Low",
    "overall_vibes": "3 - Lowkey not vibing tbh",
    "support_needed": true,
    "status": "On time"
  }
  ```