# AI-CA Individual — MVP (FastAPI + Next.js)

Features:
- Register/Login (JWT)
- Upload 1) Form 16 2) Form 26AS 3) AIS (PDFs)
- Auto-parse (heuristic) salary/interest/dividend/tds from PDFs
- Tax engine for FY 2024-25 (AY 2025-26): Old vs New + best regime + refund/payable
- Dashboard with charts (Recharts) + Parsed JSON panel
- QnA placeholder endpoint (plug llama.cpp / OpenAI later)

## Run Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # edit secrets if needed
python aica_database_initilization.py
uvicorn app.main:app --reload --port 8000
```

## Run Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev  # http://localhost:3000
```

Login/Register on `/` then open `/dashboard`. Upload PDF(s) and see the computed summary + chart.

> NOTE: Parsers are heuristic and minimal. For production accuracy, add template-based extractors for your specific Form 16/AIS formats and 26AS tables, or integrate OCR where necessary.

## Where to integrate your real AI:
- Backend: `POST /qna` in `main.py` — call your llama.cpp/OpenAI and return the answer.
- For RAG over Finance Bill/GST PDFs: add a `vectorstore/` module and index + query routes.

## DB
SQLite for dev. Switch to Postgres by setting `DATABASE_URL=postgresql+psycopg://...` and re-running migrations.