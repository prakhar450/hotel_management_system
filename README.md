# PMS — Agentic Property Management System

> A modern, AI-powered Property Management System built for independent hotels and boutique wedding venues in India. Replaces spreadsheets and WhatsApp threads with a clean staff dashboard and five purpose-built AI agents that behave like real hotel staff.

---

## What it does

- **No double bookings. Ever.** Row-level locking on every booking insert.
- **Automated booking → invoice → payment workflow** — one flow, zero manual steps.
- **Five AI agents** — Front Desk, Accounting, Inventory, Sales, and General Manager — each with a defined role, tone, and strict API permissions.
- **7 AM daily briefing** — the Manager Agent summarises occupancy, revenue, events, and alerts for the owner each morning.
- **WhatsApp notifications** via Twilio — booking confirmations, check-in reminders, payment reminders.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 |
| ORM / Migrations | SQLAlchemy + Alembic |
| AI Agents | Anthropic Claude API (`claude-sonnet-4-20250514`) |
| Frontend | React + Vite + Tailwind CSS |
| PDF generation | WeasyPrint |
| Notifications | Twilio (WhatsApp + SMS) |
| Payments | Razorpay |
| Hosting | GCP Cloud Run + Cloud SQL + Firebase Hosting |

---

## Project Structure

```
hotel_management_system/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI entry point, CORS, router registration
│   │   ├── config.py          # Environment settings (pydantic-settings)
│   │   ├── database.py        # SQLAlchemy engine, session, Base
│   │   ├── models/            # ORM models — one file per table
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── routers/           # FastAPI routers — one per domain, no business logic
│   │   ├── services/          # Business logic: booking overlap, invoicing, pricing
│   │   ├── agents/            # Agent definitions + orchestrator
│   │   └── utils/             # Invoice number generator, date helpers
│   ├── migrations/            # Alembic migrations
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── pages/             # Dashboard, Bookings, Calendar, Guests, Events…
│       ├── components/        # Shared UI components
│       └── api/               # Axios client functions (one per API endpoint)
├── docker-compose.yml         # Local dev: PostgreSQL + backend
└── CLAUDE.md                  # Full project context + build guide for AI agents
```

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.12
- Node.js 20+

### 1. Clone and configure

```bash
git clone https://github.com/prakhar450/hotel_management_system.git
cd hotel_management_system
cp backend/.env.example .env
# Fill in ANTHROPIC_API_KEY, TWILIO_*, RAZORPAY_* in .env
```

### 2. Start the database

```bash
docker-compose up -d db
```

### 3. Backend

```bash
cd backend
python3 -m venv venv
backend/venv/bin/pip install -r requirements.txt
backend/venv/bin/alembic upgrade head        # Run migrations
backend/venv/bin/python seed.py              # Seed demo data (once available)
backend/venv/bin/uvicorn app.main:app --reload  # API on http://localhost:8000
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev    # UI on http://localhost:5173
```

API docs (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)

---

## The Five Agents

| Agent | Role | Escalates when |
|---|---|---|
| **Front Desk** | Guest interactions, check-in/out, booking requests | Booking > ₹50K · Guest complaint · Overbooking risk |
| **Accounting** | Invoices, payments, reconciliation alerts | Discrepancy > ₹500 · Overdue invoice > 7 days |
| **Inventory** | Room status, event space, consumable stock | Stock below threshold · Hall conflict |
| **Sales** | Leads, wedding enquiries, quotes, follow-ups | Deal > ₹2L · Custom pricing request |
| **General Manager** | Escalations, approvals, daily 7 AM briefing | — |

All agents route through a central orchestrator. No agent talks to another directly. No agent writes to the database — they call APIs; APIs call services; services write to the DB.

---

## Build Status

| Phase | Status |
|---|---|
| Phase 0 — Environment setup | ✅ Done |
| Phase 1 — Database models & migrations | 🔄 In progress |
| Phase 2 — Core backend APIs | ⬜ Pending |
| Phase 3 — Agent layer | ⬜ Pending |
| Phase 4 — React frontend | ⬜ Pending |
| Phase 5 — Integrations (WhatsApp, PDF, Razorpay) | ⬜ Pending |
| Phase 6 — Testing | ⬜ Pending |
| Phase 7 — GCP deployment | ⬜ Pending |

---

## Key Design Rules

- `SELECT … FOR UPDATE` before every booking insert — this is the only guarantee against double bookings.
- Pricing logic lives in `services/pricing_service.py` only. AI agents can never set or change prices.
- Every agent action is logged to the `agent_logs` table. No silent failures.
- UUIDs for all customer-facing primary keys.
- Business logic in `services/`, never in `routers/`.

---

## License

Private — all rights reserved.
