# TaskFlow MVP Scaffold

FastAPI + React MVP with SQLite persistence, PDF extraction, OpenAI-compatible structured extraction, mock fallback, verification, and dashboard.

## Run backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

## Run frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173
