# Hotel PMS — Agentic Property Management System

> A modern, AI-powered Property Management System for independent hotels and boutique wedding venues in India. Replaces spreadsheets and WhatsApp threads with a clean staff dashboard and five purpose-built AI agents that behave like real hotel staff.

---

## Screenshots

**Dashboard** — Morning briefing, key stats, quick actions

![Dashboard](docs/screenshots/dashboard.jpg)

**Rooms** — Live status grid by floor, colour-coded availability

![Rooms](docs/screenshots/rooms.jpg)

**Bookings** — Full booking list with one-click check-in / check-out

![Bookings](docs/screenshots/bookings.jpg)

**Invoices** — Auto-generated invoices with status tabs and payment tracking

![Invoices](docs/screenshots/invoices.jpg)

**Inventory** — Consumables by category, low-stock alerts

![Inventory](docs/screenshots/inventory.jpg)

**Agent Chat** — Talk directly to any of the five AI agents

![Agent Chat](docs/screenshots/agents.jpg)

---

## What it does

- **No double bookings. Ever.** `SELECT … FOR UPDATE` row-level lock on every booking insert.
- **Automated booking → invoice → payment workflow** — one flow, zero manual steps.
- **Five AI agents** — Front Desk, Accounting, Inventory, Sales, and General Manager — each with a defined role, tone, and strict list of allowed API endpoints.
- **7 AM daily briefing** — the Manager Agent summarises occupancy, revenue, events, and alerts every morning.
- **Agent chat panel** — staff can ask any agent a question or assign a task directly from the dashboard.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 |
| ORM / Migrations | SQLAlchemy 2 + Alembic |
| AI Agents | Anthropic Claude API (`claude-sonnet-4-20250514`) |
| Frontend | React 18 + Vite 5 + Tailwind CSS |
| PDF generation | WeasyPrint |
| Notifications | Twilio (WhatsApp + SMS) |
| Payments | Razorpay |
| Hosting | GCP Cloud Run + Cloud SQL + Firebase Hosting |

---

## Getting Started

### Prerequisites

| Tool | Version | How to check |
|---|---|---|
| Docker Desktop | any recent | `docker --version` |
| Python | 3.11 or 3.12 | `python3 --version` |
| Node.js | 18 or 20 | `node --version` |
| Git | any | `git --version` |

> **Apple Silicon (M1/M2/M3) users:** everything below works natively on arm64 — no Rosetta needed.

---

### Step 1 — Clone the repo

```bash
git clone https://github.com/prakhar450/hotel_management_system.git
cd hotel_management_system
```

---

### Step 2 — Configure environment variables

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in the values:

```bash
# Required — the app won't start without this
DATABASE_URL=postgresql://pms_user:pms_password@localhost:5432/pms_db

# Required for AI agents to work (get one at console.anthropic.com)
ANTHROPIC_API_KEY=sk-ant-...

# Leave these as-is for local development
APP_ENV=development
SECRET_KEY=change-this-to-a-random-64-char-string
CORS_ORIGINS=http://localhost:5173

# Optional — only needed for WhatsApp notifications
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Optional — only needed for Razorpay payment links
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
```

> Without `ANTHROPIC_API_KEY`, the app runs fully — only the Agent Chat and agent confirmation panels won't produce responses.

---

### Step 3 — Start PostgreSQL

```bash
docker-compose up -d db
```

Verify it started:

```bash
docker-compose ps
# Should show: hotel_management_system-db-1   running   0.0.0.0:5432->5432/tcp
```

---

### Step 4 — Set up the backend

```bash
cd backend

# Create a Python virtual environment
python3 -m venv venv

# Install dependencies
# Important: always use venv/bin/... directly — `source venv/bin/activate`
# does not persist across terminal calls in some setups
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Run database migrations
venv/bin/alembic upgrade head

# Seed the database with demo data
# (10 rooms, 3 event spaces, 20 inventory items, 5 guests, 5 bookings, 2 events, 3 leads)
venv/bin/python seed.py

# Start the API server
venv/bin/uvicorn app.main:app --reload
```

The API is now running at **http://localhost:8000**

Swagger UI (test all endpoints interactively): **http://localhost:8000/docs**

---

### Step 5 — Set up the frontend

Open a **new terminal tab** (keep the backend running):

```bash
# From the repo root:
cd frontend

npm install
npm run dev
```

The dashboard is now at **http://localhost:5173** — open it in your browser.

---

### Verify everything is working

You should see the sidebar, today's date on the dashboard, and 10 rooms on the Rooms page.

If something looks wrong, run these checks:

```bash
# Is the backend up?
curl http://localhost:8000/health
# Expected: {"status":"ok","env":"development"}

# Did the DB seed run?
curl http://localhost:8000/api/v1/inventory/rooms | python3 -m json.tool | head -10
# Expected: a JSON array of room objects
```

---

## Project Structure

```
hotel_management_system/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI entry point, CORS, router registration
│   │   ├── config.py          # Environment settings via pydantic-settings
│   │   ├── database.py        # SQLAlchemy engine, SessionLocal, Base, get_db()
│   │   ├── models/            # ORM models — one file per table
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── routers/           # FastAPI routers — one per domain, no business logic
│   │   ├── services/          # All business logic (booking overlap, invoicing, pricing)
│   │   ├── agents/            # Five agents + orchestrator
│   │   └── utils/             # Invoice number generator, date helpers
│   ├── migrations/            # Alembic migration files
│   ├── tests/
│   ├── seed.py                # Demo data script
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── pages/             # One React page per domain (Dashboard, Rooms, Bookings…)
│       ├── components/        # AgentBubble, Layout
│       └── api/client.js      # Axios client — one function per endpoint
├── docs/screenshots/          # Product screenshots
├── docker-compose.yml         # Local dev: PostgreSQL 16
└── CLAUDE.md                  # Full architecture and build guide
```

---

## The Five Agents

All agents inherit from `base_agent.py`, which logs every call to `agent_logs`, enforces `max_tokens=1000`, and handles API errors without crashing the main booking flow. The orchestrator routes tasks and handles escalation — no agent ever talks to another directly, and no agent writes to the database.

| Agent | Role | Escalates when |
|---|---|---|
| **Front Desk** | Guest interactions, check-in/out, booking confirmation | Booking > ₹50K · Guest complaint · Overbooking risk |
| **Accounting** | Invoices, payments, reconciliation alerts | Discrepancy > ₹500 · Overdue invoice > 7 days |
| **Inventory** | Room status, event space, consumable stock | Stock below threshold · Hall conflict |
| **Sales** | Leads, wedding enquiries, quotes, follow-ups | Deal > ₹2L · Custom pricing request |
| **General Manager** | Escalations, approvals, daily 7 AM briefing | — |

---

## Key Design Rules

- `SELECT … FOR UPDATE` before every booking insert — the only guarantee against double bookings under concurrent load.
- Agents never write to the database. They call internal APIs → APIs call services → services write to DB.
- Pricing logic lives in `services/pricing_service.py` only. AI can never set or modify prices.
- Every agent action is logged to `agent_logs`. No silent failures.
- UUIDs for all customer-facing primary keys (bookings, guests, invoices, events).
- Business logic in `services/`, never in `routers/`.

---

## Build Status

| Phase | Status |
|---|---|
| Phase 0 — Environment setup | ✅ Done |
| Phase 1 — Database models & migrations | ✅ Done |
| Phase 2 — Core backend APIs | ✅ Done |
| Phase 3 — Agent layer (5 agents + orchestrator) | ✅ Done |
| Phase 4 — React frontend (10 pages) | ✅ Done |
| Phase 5 — Integrations (WhatsApp, PDF, Razorpay) | 🔲 Pending |
| Phase 6 — Testing | 🔲 Pending |
| Phase 7 — GCP deployment | 🔲 Pending |

---

## Troubleshooting

**`npm run dev` fails with `Cannot find module @rollup/rollup-darwin-arm64`**

This is an npm optional-dependency bug. Fix:

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**Backend fails to start: `could not connect to server`**

PostgreSQL isn't running. Start it first:

```bash
docker-compose up -d db
```

**`alembic upgrade head` fails: `relation already exists`**

The DB has a partial schema. Reset it cleanly:

```bash
cd backend
venv/bin/alembic downgrade base
venv/bin/alembic upgrade head
venv/bin/python seed.py
```

**Rooms / Bookings page shows no data after a fresh setup**

The seed hasn't run yet:

```bash
cd backend && venv/bin/python seed.py
```

**Agent Chat returns errors or blank responses**

`ANTHROPIC_API_KEY` in `backend/.env` is missing or invalid. All other features work without it.

---

## License

Private — all rights reserved.
