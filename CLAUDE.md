# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Dev Commands

```bash
# --- Local dev startup ---
docker-compose up -d db                        # Start PostgreSQL 16 on :5432
cd backend && uvicorn app.main:app --reload    # Backend on :8000 (uses venv)
cd frontend && npm run dev                     # Frontend on :5173

# --- Python (always use the venv) ---
backend/venv/bin/python                        # Python interpreter
backend/venv/bin/pip install -r backend/requirements.txt

# --- Database migrations ---
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1                           # Roll back one migration
alembic downgrade base && alembic upgrade head && python seed.py  # Full reset

# --- Tests ---
cd backend && backend/venv/bin/pytest tests/                      # All tests
cd backend && backend/venv/bin/pytest tests/test_bookings.py -k "test_overlap"  # Single test

# --- API docs (Swagger UI) ---
open http://localhost:8000/docs
```

> **venv note:** `source venv/bin/activate` does not persist across shell calls in Claude Code.
> Always use `backend/venv/bin/python` / `backend/venv/bin/pip` / `backend/venv/bin/pytest` directly.

---

## Architecture Overview

This is a **FastAPI + PostgreSQL + React** SaaS PMS with an agentic AI layer. The repo layout is:

```
hotel_management_system/
├── backend/app/
│   ├── main.py          — FastAPI app, CORS, router registration
│   ├── config.py        — pydantic-settings, reads .env
│   ├── database.py      — SQLAlchemy engine, SessionLocal, Base, get_db()
│   ├── models/          — SQLAlchemy ORM models (one file per table)
│   ├── schemas/         — Pydantic request/response schemas (mirrors models/)
│   ├── routers/         — FastAPI routers; one per domain, no business logic here
│   ├── services/        — All business logic (booking overlap, invoice calc, pricing)
│   ├── agents/          — Agent definitions + orchestrator
│   └── utils/           — Invoice number generator, date helpers
├── backend/migrations/  — Alembic migration files
├── backend/tests/
├── frontend/src/
│   ├── pages/           — One React page per domain
│   ├── components/      — Shared UI components
│   └── api/             — Axios client functions (one per endpoint, never call APIs from components)
└── docker-compose.yml   — Local: postgres + backend services
```

### Key invariants Claude must never break
1. **No double bookings** — `POST /bookings` must `SELECT … FOR UPDATE` before insert.
2. **Agents never write to DB** — agents call internal APIs; APIs call services; services write to DB.
3. **Pricing lives in `services/pricing_service.py` only** — agents cannot set or modify prices.
4. **Every agent call is logged** — `agent_logs` table, no exceptions.
5. **Business logic in `services/`, never in `routers/`.**
6. **UUIDs for all customer-facing PKs** — prevents enumeration attacks.

### Agent architecture
All five agents (`front_desk`, `accounting`, `inventory`, `sales`, `manager`) inherit from `base_agent.py`, which holds the Anthropic client, auto-logs every call to `agent_logs`, and enforces `max_tokens=1000`. The `orchestrator.py` routes tasks to the correct agent and handles escalation (`ESCALATE` → Manager Agent). Agents communicate only through the orchestrator — never directly with each other.

### Request flow
```
React page → /api/ axios fn → FastAPI router → service layer → SQLAlchemy → PostgreSQL
                                    ↓
                           agents/orchestrator → base_agent → Claude API
                                    ↓
                              agent_logs table
```

---

# Agentic Property Management System — Master Project Document
### Context & Build Guide for Claude Code Agents

---

> Work through the checklist in order. Do not skip phases. Mark items `[x]` as you complete them.

---

## 1. WHAT WE ARE BUILDING

A **hotel and wedding venue Property Management System (PMS)** with an agentic AI layer.
The system replaces spreadsheets and WhatsApp threads for independent hotels and boutique
wedding venues in India. It is sold as a SaaS product.

### The core promise to the client
- Automated booking → invoice → payment workflow
- AI agents that behave like real hotel staff (front desk, accounting, inventory, sales, manager)
- No double bookings. Ever.
- A dashboard the owner can check on their phone at 7am

### Current status
- Architecture designed, decisions made
- No code written yet
- Demo needed for first paying client — prioritise demo-readiness

### What makes this different from existing PMS (Opera, IDS, etc.)
- Built for independent properties (not 500-room chains)
- AI agents draft guest communications, flag risks, surface insights
- Lightweight, fast to set up, affordable
- Agents reason over partial information — they don't just return yes/no

---

## 2. ARCHITECTURE DECISIONS (FINAL — DO NOT CHANGE THESE)

These decisions are locked. Do not suggest alternatives unless there is a critical blocker.

| Layer | Technology | Reason |
|---|---|---|
| Backend | FastAPI (Python) | Async, fast, excellent for AI agent orchestration |
| Database | PostgreSQL | Transactions, row-level locking, audit trail |
| ORM | SQLAlchemy + Alembic | Industry standard, migration support |
| Agent LLM | Anthropic Claude API (claude-sonnet-4-20250514) | Best reasoning, tool use |
| Frontend | React + Vite + Tailwind CSS | Fast build, modern UI |
| Hosting | GCP Cloud Run (backend) + Cloud SQL (DB) + Firebase Hosting (frontend) |
| Secrets | GCP Secret Manager | API keys, DB credentials |
| Containerisation | Docker | Required for Cloud Run |
| PDF generation | WeasyPrint (Python) | Invoices, reports |
| Notifications | Twilio (WhatsApp + SMS) | Guest communications |
| Payments | Razorpay | India-first payment gateway |

### Core Architectural Rules (NEVER violate these)
1. **Agents never talk to each other directly.** All agent calls route through the FastAPI orchestrator.
2. **Agents never write to the database directly.** They call APIs. APIs write to the DB.
3. **Pricing logic lives in backend code only.** AI never sets or modifies prices.
4. **Every agent action is logged.** Table: `agent_logs`. No exceptions.
5. **Row locking prevents double bookings.** Always use `SELECT ... FOR UPDATE` before any booking insert.
6. **Each agent has a strict list of allowed API endpoints.** It cannot call anything outside that list.
7. **Manual override always exists.** Staff can override any agent decision from the dashboard.

---

## 3. THE FIVE AGENTS

### Agent 1 — Front Desk Agent
**Role:** Handles all guest-facing interactions, check-in/check-out, booking requests.
**Allowed APIs:** `GET /availability/rooms`, `POST /bookings`, `GET /guests`, `POST /guests`, `PUT /bookings/{id}/checkin`, `PUT /bookings/{id}/checkout`
**Tone:** Warm, professional, concise. Like a well-trained hotel receptionist.
**Escalates to Manager when:** Booking value > ₹50,000 | Guest complaint | Overbooking risk

### Agent 2 — Accounting Agent
**Role:** Invoices, payments, financial reports, reconciliation alerts.
**Allowed APIs:** `POST /invoices`, `GET /invoices/{id}`, `POST /payments`, `GET /reports/revenue`
**Tone:** Precise, formal. Like a careful accountant.
**Escalates to Manager when:** Payment discrepancy > ₹500 | Overdue invoice > 7 days

### Agent 3 — Inventory Agent
**Role:** Tracks room status, event space availability, consumable stock (chairs, linen, crockery, AV).
**Allowed APIs:** `GET /inventory/rooms`, `GET /inventory/spaces`, `GET /inventory/consumables`, `POST /inventory/reserve`, `POST /inventory/release`, `GET /inventory/alerts`
**Tone:** Matter-of-fact. Returns structured data + plain-language summary.
**Escalates to Manager when:** Consumable stock below threshold | Hall conflict detected

### Agent 4 — Sales Agent
**Role:** Manages event leads, wedding enquiries, site visit scheduling, quotes, follow-ups.
**Allowed APIs:** `POST /leads`, `GET /leads`, `PUT /leads/{id}`, `POST /events`, `GET /availability/spaces`, `POST /quotes`
**Tone:** Enthusiastic but not pushy. Like a good sales coordinator.
**Escalates to Manager when:** Deal value > ₹2,00,000 | Client requests custom pricing

### Agent 5 — General Manager Agent
**Role:** Reviews escalations, approves high-value transactions, gets daily briefings, sees all alerts.
**Allowed APIs:** All read endpoints + `POST /approvals`, `PUT /bookings/{id}/override`, `GET /reports/*`
**Tone:** Executive. Summarises, decides, delegates.
**Auto-briefs at:** 7:00 AM daily (occupancy, revenue, today's events, pending alerts)

---

## 4. DATABASE SCHEMA

### Tables to create (in this order due to foreign keys)

```
guests           → base table, no dependencies
rooms            → base table
event_spaces     → base table
inventory_items  → base table
bookings         → depends on guests, rooms
events           → depends on guests, event_spaces
invoices         → depends on bookings OR events
payments         → depends on invoices
inventory_usage  → depends on events, inventory_items
agent_logs       → depends on nothing (standalone audit table)
tasks            → depends on nothing (agent task queue)
leads            → depends on nothing (sales pipeline)
quotes           → depends on leads, event_spaces
```

### Key fields per table

**guests:** id (UUID), name, phone (unique), email, id_type, id_number, address, nationality, created_at, notes

**rooms:** id, room_number (unique), type (single/double/suite/deluxe), floor, base_rate, status (available/occupied/maintenance/blocked), amenities (JSONB), created_at

**event_spaces:** id, name, type (hall/lawn/terrace), capacity, base_rate_per_day, base_rate_per_slot, setup_time_hours, teardown_time_hours, amenities (JSONB), status

**bookings:** id (UUID), guest_id (FK), room_id (FK), check_in (date), check_out (date), actual_checkin (timestamp), actual_checkout (timestamp), status (enquiry/confirmed/checked_in/checked_out/cancelled/no_show), adults, children, special_requests, source (walk_in/phone/online/agent), created_by, created_at

**events:** id (UUID), name, event_type (wedding/corporate/birthday/social), guest_id (FK), space_id (FK), event_date (date), start_time, end_time, guest_count, status (enquiry/confirmed/in_progress/completed/cancelled), special_requirements, created_at

**invoices:** id (UUID), invoice_number (unique, auto-generated), booking_id (FK nullable), event_id (FK nullable), subtotal, tax_amount, discount_amount, total_amount, status (draft/sent/paid/overdue/cancelled), due_date, line_items (JSONB), created_at

**payments:** id (UUID), invoice_id (FK), amount, method (cash/upi/card/bank_transfer/cheque), reference_number, recorded_by, payment_date, notes, created_at

**inventory_items:** id, name, category (linen/furniture/av/crockery/decor/other), total_quantity, available_quantity, low_stock_threshold, unit, notes

**inventory_usage:** id, event_id (FK), item_id (FK), quantity_used, return_date, notes

**agent_logs:** id (UUID), agent_name, action, input_data (JSONB), output_data (JSONB), api_endpoint, success (bool), error_message, duration_ms, created_at

**tasks:** id, title, assigned_to_agent, status (pending/in_progress/done/escalated), priority (low/medium/high/urgent), due_at, context (JSONB), created_at

**leads:** id (UUID), name, phone, email, event_type, event_date, guest_count, budget_range, source, status (new/contacted/site_visit/quoted/won/lost), notes, created_at, last_contacted_at

**quotes:** id (UUID), lead_id (FK), space_id (FK), total_amount, valid_until, line_items (JSONB), status (draft/sent/accepted/rejected), created_at

---

## 5. API ENDPOINTS (COMPLETE LIST)

### Booking endpoints
```
POST   /api/v1/bookings                    — Create booking
GET    /api/v1/bookings                    — List bookings (filters: date, status, room)
GET    /api/v1/bookings/{id}               — Get single booking
PUT    /api/v1/bookings/{id}               — Update booking
PUT    /api/v1/bookings/{id}/checkin       — Record check-in
PUT    /api/v1/bookings/{id}/checkout      — Record check-out
PUT    /api/v1/bookings/{id}/cancel        — Cancel booking
PUT    /api/v1/bookings/{id}/override      — Manager override
```

### Availability endpoints
```
GET    /api/v1/availability/rooms          — Rooms available for date range
GET    /api/v1/availability/spaces         — Event spaces available for date/time slot
GET    /api/v1/calendar                    — Full calendar view (bookings + events)
```

### Guest endpoints
```
POST   /api/v1/guests                      — Create guest
GET    /api/v1/guests                      — Search guests
GET    /api/v1/guests/{id}                 — Get guest profile
PUT    /api/v1/guests/{id}                 — Update guest
GET    /api/v1/guests/{id}/history         — Guest booking history
```

### Event endpoints
```
POST   /api/v1/events                      — Create event
GET    /api/v1/events                      — List events
GET    /api/v1/events/{id}                 — Get event
PUT    /api/v1/events/{id}                 — Update event
PUT    /api/v1/events/{id}/cancel          — Cancel event
```

### Invoice and payment endpoints
```
POST   /api/v1/invoices                    — Generate invoice
GET    /api/v1/invoices/{id}               — Get invoice
PUT    /api/v1/invoices/{id}               — Update invoice
GET    /api/v1/invoices/{id}/pdf           — Download PDF
POST   /api/v1/payments                    — Record payment
GET    /api/v1/payments                    — List payments
```

### Inventory endpoints
```
GET    /api/v1/inventory/rooms             — Room status overview
GET    /api/v1/inventory/spaces            — Space availability
GET    /api/v1/inventory/consumables       — Stock levels
POST   /api/v1/inventory/reserve           — Reserve items for event
POST   /api/v1/inventory/release           — Release reserved items
GET    /api/v1/inventory/alerts            — Low stock + conflict alerts
PUT    /api/v1/inventory/items/{id}        — Update stock count
```

### Sales / leads endpoints
```
POST   /api/v1/leads                       — Create lead
GET    /api/v1/leads                       — List leads (filter by status)
PUT    /api/v1/leads/{id}                  — Update lead
POST   /api/v1/quotes                      — Generate quote
GET    /api/v1/quotes/{id}/pdf             — Download quote PDF
```

### Reports endpoints
```
GET    /api/v1/reports/revenue             — Revenue by date range
GET    /api/v1/reports/occupancy           — Room occupancy rate
GET    /api/v1/reports/events              — Event summary
GET    /api/v1/reports/daily-briefing      — Manager morning summary
```

### Agent endpoint (internal orchestrator)
```
POST   /api/v1/agent/invoke                — Invoke an agent with a task + context
GET    /api/v1/agent/logs                  — View agent action history
```

---

## 6. PROJECT FOLDER STRUCTURE

```
pms/
├── backend/
│   ├── app/
│   │   ├── main.py                  — FastAPI app entry point
│   │   ├── config.py                — Settings, env vars
│   │   ├── database.py              — DB connection, session
│   │   ├── models/                  — SQLAlchemy models (one file per table)
│   │   │   ├── guest.py
│   │   │   ├── room.py
│   │   │   ├── booking.py
│   │   │   ├── event.py
│   │   │   ├── invoice.py
│   │   │   ├── payment.py
│   │   │   ├── inventory.py
│   │   │   ├── lead.py
│   │   │   └── agent_log.py
│   │   ├── schemas/                 — Pydantic request/response schemas
│   │   │   └── (mirrors models/)
│   │   ├── routers/                 — FastAPI routers (one file per domain)
│   │   │   ├── bookings.py
│   │   │   ├── guests.py
│   │   │   ├── events.py
│   │   │   ├── invoices.py
│   │   │   ├── payments.py
│   │   │   ├── inventory.py
│   │   │   ├── availability.py
│   │   │   ├── leads.py
│   │   │   ├── reports.py
│   │   │   └── agent.py
│   │   ├── agents/                  — Agent definitions and orchestrator
│   │   │   ├── orchestrator.py      — Routes tasks to agents
│   │   │   ├── base_agent.py        — Base class all agents inherit
│   │   │   ├── front_desk.py
│   │   │   ├── accounting.py
│   │   │   ├── inventory.py
│   │   │   ├── sales.py
│   │   │   └── manager.py
│   │   ├── services/                — Business logic layer
│   │   │   ├── booking_service.py   — Overlap check, locking logic
│   │   │   ├── invoice_service.py   — Auto-generation, PDF
│   │   │   ├── notification_service.py  — Twilio calls
│   │   │   └── pricing_service.py   — Fixed pricing rules
│   │   └── utils/
│   │       ├── invoice_number.py    — INV-2025-0001 generator
│   │       └── date_helpers.py
│   ├── migrations/                  — Alembic migration files
│   ├── tests/
│   │   ├── test_bookings.py
│   │   ├── test_agents.py
│   │   └── test_availability.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic.ini
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        — Morning summary, key metrics
│   │   │   ├── Bookings.jsx         — Booking list + create
│   │   │   ├── Calendar.jsx         — Full calendar view
│   │   │   ├── Guests.jsx           — Guest directory
│   │   │   ├── Events.jsx           — Event/wedding management
│   │   │   ├── Inventory.jsx        — Room + stock status
│   │   │   ├── Invoices.jsx         — Invoice list + PDF
│   │   │   ├── Leads.jsx            — Sales pipeline
│   │   │   ├── Reports.jsx          — Revenue charts
│   │   │   └── AgentLogs.jsx        — Agent activity feed
│   │   ├── components/
│   │   │   ├── BookingForm.jsx
│   │   │   ├── GuestSearch.jsx
│   │   │   ├── RoomCard.jsx
│   │   │   ├── InvoiceCard.jsx
│   │   │   └── AlertBanner.jsx
│   │   ├── api/                     — Axios API client functions
│   │   └── App.jsx
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
│
├── docker-compose.yml               — Local dev: backend + postgres
├── .env                             — Never commit this
└── README.md
```

---

## 7. ENVIRONMENT VARIABLES

```bash
# .env.example — copy to .env and fill in

# Database
DATABASE_URL=postgresql://pms_user:password@localhost:5432/pms_db

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Twilio (notifications)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Razorpay
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=

# App settings
APP_ENV=development
SECRET_KEY=generate-a-random-64-char-string
CORS_ORIGINS=http://localhost:5173

# GCP (production only)
GCP_PROJECT_ID=
GCP_REGION=asia-south1
```

---

## 8. COMPLETE TO-DO LIST

Work through these **in order**. Do not jump phases.
Items marked `[DEMO]` are the minimum needed for the client demo.
Items marked `[CRITICAL]` will cause data loss or double-bookings if skipped.

---

### PHASE 0 — LOCAL ENVIRONMENT SETUP

- [ ] Create project root folder `pms/`
- [ ] Initialise git repo (`git init`)
- [ ] Create `.gitignore` (include `.env`, `__pycache__`, `node_modules`, `*.pyc`)
- [ ] Create `backend/` and `frontend/` directories
- [ ] Create `docker-compose.yml` with PostgreSQL 16 service and backend service
- [ ] Set up Python virtual environment (`python -m venv venv`)
- [ ] Create `backend/requirements.txt` with: fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary, pydantic, pydantic-settings, anthropic, python-dotenv, weasyprint, razorpay, twilio, python-jose, passlib, python-multipart
- [ ] Install all Python dependencies
- [ ] Copy `.env.example` to `.env` and fill in local values
- [ ] Verify PostgreSQL is running via Docker (`docker-compose up -d db`)
- [ ] Confirm DB connection works from Python

---

### PHASE 1 — DATABASE (CRITICAL — DO THIS BEFORE ANY API WORK)

- [ ] `[CRITICAL]` Create `backend/app/database.py` — SQLAlchemy engine, SessionLocal, Base, get_db dependency
- [ ] `[CRITICAL]` Initialise Alembic (`alembic init migrations`)
- [ ] `[CRITICAL]` Configure `alembic.ini` to read DATABASE_URL from `.env`
- [ ] Create SQLAlchemy model: `guests` (with all fields from schema section)
- [ ] Create SQLAlchemy model: `rooms`
- [ ] Create SQLAlchemy model: `event_spaces`
- [ ] Create SQLAlchemy model: `inventory_items`
- [ ] `[CRITICAL]` Create SQLAlchemy model: `bookings` (with foreign keys to guests, rooms)
- [ ] Create SQLAlchemy model: `events` (with foreign keys to guests, event_spaces)
- [ ] `[CRITICAL]` Create SQLAlchemy model: `invoices` (nullable FK to both bookings and events)
- [ ] Create SQLAlchemy model: `payments` (FK to invoices)
- [ ] Create SQLAlchemy model: `inventory_usage` (FK to events and inventory_items)
- [ ] `[CRITICAL]` Create SQLAlchemy model: `agent_logs` (standalone audit table)
- [ ] Create SQLAlchemy model: `tasks`
- [ ] Create SQLAlchemy model: `leads`
- [ ] Create SQLAlchemy model: `quotes` (FK to leads and event_spaces)
- [ ] `[CRITICAL]` Generate first Alembic migration (`alembic revision --autogenerate -m "initial schema"`)
- [ ] `[CRITICAL]` Review the generated migration SQL — confirm all tables and indexes are correct
- [ ] `[CRITICAL]` Add database indexes on: `bookings.room_id + check_in + check_out`, `bookings.guest_id`, `invoices.booking_id`, `invoices.event_id`, `payments.invoice_id`, `agent_logs.created_at`
- [ ] `[CRITICAL]` Run migration (`alembic upgrade head`)
- [ ] Seed test data: 10 rooms (mixed types), 3 event spaces, 20 inventory items, 5 test guests
- [ ] Write a seed script `backend/seed.py` so database can be reset during dev

---

### PHASE 2 — CORE BACKEND APIS

#### FastAPI setup
- [ ] Create `backend/app/main.py` with FastAPI app, CORS middleware, router registration, health check endpoint
- [ ] Create `backend/app/config.py` using pydantic-settings to load `.env`
- [ ] Create Pydantic schemas for every model (request + response schemas separate)

#### Availability API (build this first — everything depends on it)
- [ ] `[DEMO]` `[CRITICAL]` Implement `GET /api/v1/availability/rooms` — query rooms NOT in `bookings` table for the given date range, accounting for turnaround buffer (configurable, default 2 hours)
- [ ] `[DEMO]` `[CRITICAL]` Write the overlap detection query: `check_in < requested_checkout AND check_out > requested_checkin` — test this with overlapping, adjacent, and non-overlapping cases
- [ ] `[DEMO]` Implement `GET /api/v1/availability/spaces` — query spaces NOT in `events` table for the given date + time slot (include setup and teardown buffer times)
- [ ] Implement `GET /api/v1/calendar` — return all bookings + events for a month in a format the frontend calendar can consume

#### Guests API
- [ ] `[DEMO]` Implement `POST /api/v1/guests` — create guest, check for duplicate phone number
- [ ] `[DEMO]` Implement `GET /api/v1/guests` — search by name or phone (partial match)
- [ ] Implement `GET /api/v1/guests/{id}` — single guest profile
- [ ] Implement `PUT /api/v1/guests/{id}` — update guest
- [ ] Implement `GET /api/v1/guests/{id}/history` — all past bookings + events for this guest

#### Bookings API
- [ ] `[DEMO]` `[CRITICAL]` Implement `POST /api/v1/bookings` — full booking creation flow:
  - Validate check-in < check-out
  - `SELECT room FOR UPDATE` (row lock)
  - Re-check availability within the lock
  - Insert booking
  - Trigger invoice auto-generation
  - Release lock
  - Return booking with invoice
- [ ] `[DEMO]` Implement `GET /api/v1/bookings` with filters (date range, status, room number)
- [ ] Implement `GET /api/v1/bookings/{id}`
- [ ] `[DEMO]` Implement `PUT /api/v1/bookings/{id}/checkin` — set actual_checkin timestamp, update room status to occupied
- [ ] `[DEMO]` Implement `PUT /api/v1/bookings/{id}/checkout` — set actual_checkout timestamp, update room status to available
- [ ] Implement `PUT /api/v1/bookings/{id}/cancel` — update status, trigger invoice cancellation logic
- [ ] Implement `PUT /api/v1/bookings/{id}/override` — manager-only override

#### Events API
- [ ] `[DEMO]` Implement `POST /api/v1/events` — create event with space reservation
- [ ] `[DEMO]` Implement `GET /api/v1/events` with date filter
- [ ] Implement `PUT /api/v1/events/{id}`
- [ ] Implement `PUT /api/v1/events/{id}/cancel`

#### Invoice + Payment API
- [ ] `[DEMO]` `[CRITICAL]` Create `backend/app/services/invoice_service.py`:
  - Auto-generate invoice number (format: INV-YYYY-NNNN, sequential, never repeat)
  - Calculate line items from booking (room rate × nights) or event (space rate + additional services)
  - Apply GST (18% for services — verify current rate)
  - Set due date (configurable, default: 7 days)
- [ ] `[DEMO]` Implement `POST /api/v1/invoices` — create invoice
- [ ] Implement `GET /api/v1/invoices/{id}`
- [ ] Implement `GET /api/v1/invoices/{id}/pdf` — generate PDF using WeasyPrint, return as file response
- [ ] Create invoice PDF HTML template (professional, includes property logo placeholder, guest details, line items, tax breakdown, payment instructions)
- [ ] `[DEMO]` Implement `POST /api/v1/payments` — record payment, update invoice status (partial/paid), log payment method
- [ ] Add logic to mark invoice as `paid` when sum of payments = total_amount
- [ ] Add logic to mark invoice as `overdue` when due_date passes and not paid (can be a scheduled task or checked on read)

#### Inventory API
- [ ] `[DEMO]` Implement `GET /api/v1/inventory/rooms` — current status of all rooms
- [ ] Implement `GET /api/v1/inventory/consumables` — stock levels with low-stock flag
- [ ] `[CRITICAL]` Implement `POST /api/v1/inventory/reserve` — reduce available_quantity for event, with check for sufficient stock
- [ ] Implement `POST /api/v1/inventory/release` — restore quantity when event cancelled
- [ ] `[DEMO]` Implement `GET /api/v1/inventory/alerts` — rooms in maintenance, low stock items, upcoming events with potential stock issues

#### Sales / Leads API
- [ ] `[DEMO]` Implement `POST /api/v1/leads` — create lead
- [ ] `[DEMO]` Implement `GET /api/v1/leads` with status filter
- [ ] Implement `PUT /api/v1/leads/{id}` — update status, notes
- [ ] Implement `POST /api/v1/quotes` — generate quote PDF for a lead

#### Reports API
- [ ] `[DEMO]` Implement `GET /api/v1/reports/daily-briefing` — returns: today's check-ins, check-outs, active events, revenue today, pending alerts, upcoming in 7 days
- [ ] Implement `GET /api/v1/reports/revenue` — daily/monthly revenue, breakdown by room vs events
- [ ] Implement `GET /api/v1/reports/occupancy` — occupancy % by date range

---

### PHASE 3 — AGENT LAYER

- [ ] Create `backend/app/agents/base_agent.py`:
  - Holds the Anthropic client
  - Method: `invoke(task: str, context: dict) → str`
  - Auto-logs every call to `agent_logs` table
  - Handles API errors gracefully (never crash the booking flow)
  - Max tokens: 1000 per agent call (cost control)
  - Temperature: 0.3 (consistent, not creative)

- [ ] Create `backend/app/agents/orchestrator.py`:
  - Routes incoming task to the correct agent based on task type
  - Passes only the minimal context needed (not the full DB dump)
  - Handles escalation: if agent returns `ESCALATE`, route to Manager Agent
  - All orchestrator actions logged

- [ ] `[DEMO]` Create `backend/app/agents/front_desk.py`:
  - System prompt: defines role, tone, and allowed actions
  - Handles: availability queries in natural language, booking confirmations, guest communications
  - Tool definitions for its allowed API endpoints
  - Returns structured response (action taken + message to guest)

- [ ] `[DEMO]` Create `backend/app/agents/inventory.py`:
  - System prompt focuses on availability checking, conflict detection, alert generation
  - After every booking, runs a proactive scan for the next 7 days
  - Returns: availability verdict + plain-language explanation + any warnings

- [ ] Create `backend/app/agents/accounting.py`:
  - Handles invoice queries, payment reminders, discrepancy detection
  - Never modifies prices — only reads and reports
  - Can draft WhatsApp payment reminder messages

- [ ] Create `backend/app/agents/sales.py`:
  - Handles lead follow-up suggestions, quote generation context
  - Tracks time since last contact, suggests next action

- [ ] `[DEMO]` Create `backend/app/agents/manager.py`:
  - Receives escalations from all agents
  - Generates morning briefing (called at 7am or on demand)
  - Has read access to all data, can approve/reject

- [ ] `[DEMO]` Create `POST /api/v1/agent/invoke` endpoint — accepts {agent_name, task, context}, invokes agent, returns response
- [ ] Create `GET /api/v1/agent/logs` — paginated agent activity log for the dashboard

---

### PHASE 4 — REACT FRONTEND DASHBOARD

#### Setup
- [ ] Scaffold frontend with Vite + React (`npm create vite@latest frontend -- --template react`)
- [ ] Install Tailwind CSS and configure
- [ ] Install: axios, react-router-dom, react-query (or SWR), date-fns, recharts
- [ ] Create Axios API client with base URL from env, error handling, loading states
- [ ] Set up React Router with all page routes
- [ ] Create basic layout: sidebar nav + top bar + main content area

#### Pages (build in this order)
- [ ] `[DEMO]` **Dashboard page** — morning briefing card, today's check-ins/check-outs table, active alerts banner, quick action buttons (New Booking, New Guest, Record Payment)
- [ ] `[DEMO]` **Rooms page** — grid of room cards showing room number, type, current status (colour-coded: green=available, orange=occupied, grey=maintenance), click to see current guest
- [ ] `[DEMO]` **New Booking flow** — Step 1: date picker + room type selector → Step 2: guest search/create → Step 3: confirm + see generated invoice
- [ ] `[DEMO]` **Bookings list** — filterable table (date, status, room), click to open booking detail
- [ ] `[DEMO]` **Check-in / Check-out buttons** on booking detail page — one click, confirms with agent response
- [ ] **Calendar page** — month view, bookings shown as coloured bars per room, events shown on event space rows
- [ ] **Guest directory** — searchable by name/phone, guest card with booking history
- [ ] `[DEMO]` **Events / Weddings page** — list of upcoming events, status badges, click to see details
- [ ] `[DEMO]` **Invoices page** — list with status filter (draft/sent/paid/overdue), PDF download button per row
- [ ] `[DEMO]` **Record Payment** — modal/form: select invoice, enter amount, method, reference number
- [ ] **Inventory page** — room status grid, consumables table with low-stock highlights, alerts list
- [ ] **Leads / Sales page** — Kanban-style columns (New → Contacted → Quoted → Won/Lost)
- [ ] **Agent Logs page** — activity feed showing every agent action (what was asked, what was decided, timestamp)
- [ ] **Reports page** — Revenue bar chart (daily/monthly), occupancy % gauge, events summary

#### UI polish (for demo)
- [ ] `[DEMO]` Add loading spinners on all data fetch states
- [ ] `[DEMO]` Add error states with user-friendly messages
- [ ] `[DEMO]` Add success toast notifications for: booking created, payment recorded, check-in done
- [ ] Make all tables responsive (horizontal scroll on mobile)
- [ ] Add property name to top bar (configurable from env or settings)

---

### PHASE 5 — INTEGRATIONS

- [ ] **WhatsApp notifications via Twilio:**
  - Booking confirmation to guest (with invoice total)
  - Check-in reminder (day before)
  - Payment reminder for overdue invoices
  - Create `backend/app/services/notification_service.py` with send_whatsapp(phone, message) function
  - All notifications logged (never fail silently)

- [ ] **PDF generation:**
  - Invoice PDF: professional layout, property details, guest details, line items, tax, total, payment instructions, QR code placeholder for UPI
  - Quote PDF: similar to invoice but marked QUOTATION, valid-until date, terms

- [ ] **Razorpay integration (optional for demo, required for launch):**
  - Create payment link from invoice
  - Webhook to auto-record payment when Razorpay confirms

---

### PHASE 6 — TESTING

- [ ] `[CRITICAL]` Write test: create booking → verify no double booking possible for same room+dates (run 2 concurrent requests)
- [ ] `[CRITICAL]` Write test: partial payment → invoice stays open. Full payment → invoice auto-closes
- [ ] Write test: cancel booking → room status returns to available
- [ ] Write test: event space — same hall, overlapping time → second booking rejected
- [ ] Write test: inventory reserve → available_quantity decreases. release → restores
- [ ] Write test: agent log — every agent call creates a log entry
- [ ] Manual test: full booking flow end-to-end (create guest → book room → check in → record payment → check out)
- [ ] Manual test: full event flow (create lead → convert to event → generate invoice → record payment)
- [ ] Load test: 10 simultaneous booking requests for the same room on the same date — only 1 should succeed

---

### PHASE 7 — DEPLOYMENT TO GCP

- [ ] Create GCP project
- [ ] Enable APIs: Cloud Run, Cloud SQL, Secret Manager, Artifact Registry, Cloud Build
- [ ] Create Cloud SQL PostgreSQL 16 instance (db-f1-micro to stay within $300 budget)
- [ ] Create production database and user
- [ ] Run Alembic migrations against Cloud SQL
- [ ] Store all secrets in Secret Manager: DATABASE_URL, ANTHROPIC_API_KEY, TWILIO credentials, RAZORPAY credentials, SECRET_KEY
- [ ] Write `backend/Dockerfile`
- [ ] Build and push Docker image to Artifact Registry
- [ ] Deploy backend to Cloud Run (--min-instances=0, --max-instances=5, --memory=512Mi)
- [ ] Set Cloud Run environment variables to pull from Secret Manager
- [ ] Verify backend health check returns 200 at Cloud Run URL
- [ ] Build frontend (`npm run build`)
- [ ] Deploy frontend to Firebase Hosting
- [ ] Set CORS_ORIGINS in backend to Firebase Hosting URL
- [ ] Run full end-to-end test on production URLs
- [ ] Set up Cloud Run domain mapping (optional custom domain)
- [ ] Set up GCP budget alert at $200 (leave buffer before $300 limit)

---

### PHASE 8 — DEMO PREPARATION

- [ ] Seed demo database with realistic data: 15 rooms (actual room types), 3 event spaces (Grand Hall, Lawn A, Rooftop Terrace), 30 inventory items, 10 guests, 5 upcoming bookings, 2 upcoming weddings
- [ ] Prepare demo script (5 scenarios to walk through with client)
- [ ] Test all demo scenarios back to back without errors
- [ ] Have a backup: if live demo has issues, have screen recordings of each scenario
- [ ] Brief: prepare a one-page leave-behind for the client (what the system does, pricing, next steps)

---

## 9. BEST PRACTICES

### Code quality
- Write Pydantic schemas for every request and response — no raw dict passing between layers
- Use SQLAlchemy sessions properly — always close sessions, use `with` context or FastAPI dependency injection
- Never put business logic in routers — it goes in services/
- Every function that touches the DB should have a docstring explaining what it does and why
- Commit frequently with meaningful messages: `feat: add booking overlap detection` not `update`
- Use type hints everywhere in Python

### Database
- Never run raw SQL strings — use SQLAlchemy ORM or parameterised queries (prevents SQL injection)
- Every table must have `created_at` and `updated_at` timestamps — add a SQLAlchemy event listener so `updated_at` auto-updates
- Use UUIDs for all primary keys on customer-facing tables (bookings, guests, invoices, events) — prevents enumeration attacks
- Index every foreign key column and every column you will filter or ORDER BY
- Never delete records — use a `status` field or `deleted_at` soft delete

### Agent design
- Keep prompts short and specific — long prompts waste tokens and confuse the model
- Always include the property's current context in agent prompts (today's date, property name, any relevant state)
- Never trust agent output to modify prices, apply discounts, or change core business data directly — always validate through the service layer
- Set a timeout on agent calls (10 seconds max) — if the LLM is slow, the booking flow should not hang
- Log the raw prompt + response for every agent call — you will need this for debugging

### Security
- Never commit `.env` to git — ever
- All API endpoints that modify data require authentication (add JWT auth in Phase 2, even if simple)
- Rate-limit the agent/invoke endpoint — it calls an external LLM and can be expensive
- Validate and sanitise all inputs at the Pydantic schema level before they touch the DB
- Store Anthropic and Razorpay keys in GCP Secret Manager — never in environment variables in production

### Cost management
- Set `max_tokens: 1000` on all Claude API calls — most agent responses need far less
- Cache the daily briefing (generate once at 7am, serve from cache until next day)
- Use Cloud Run `--min-instances=0` during initial period — cold start is ~1–2 seconds, acceptable for an internal tool
- Monitor Cloud Run and Claude API costs weekly during the first month

---

## 10. WHAT NOT TO DO

These are mistakes that will cost you hours or break the product. Read carefully.

### Agent mistakes
- **Do not let agents make autonomous decisions about pricing, discounts, or refunds.** They can suggest, never act.
- **Do not pass entire database dumps to agents.** Only pass the specific context needed for the task.
- **Do not let agents retry endlessly.** One failed call → log it → fallback to manual action. Don't loop.
- **Do not design agents to talk to each other.** All coordination goes through the orchestrator. Agent-to-agent calls create unpredictable loops.
- **Do not assume the agent response is always valid JSON.** Always parse defensively with try/except.

### Database mistakes
- **Do not skip the row lock (`SELECT FOR UPDATE`) when creating bookings or reserving inventory.** This is the only thing preventing double bookings in concurrent scenarios.
- **Do not use `WidthType.PERCENTAGE` in database queries.** (This is a docx rule — ignore in DB context.)
- **Do not put computed fields (like "invoice total") in the DB.** Calculate them in the service layer. Denormalised computed data gets out of sync.
- **Do not create migrations manually.** Always use `alembic revision --autogenerate` and then review and edit the output.
- **Do not run `alembic upgrade head` on production without first testing on a staging/local DB.**

### API design mistakes
- **Do not expose internal database IDs (auto-increment integers) in public API responses.** Use UUIDs for all client-facing IDs.
- **Do not return passwords, secret keys, or internal credentials in any API response.** Ever.
- **Do not skip input validation.** A check-in date of "yesterday" or a negative payment amount will cause nonsensical data if you don't validate.
- **Do not write one giant router file.** One router per domain. Router files should only route — no logic.

### Frontend mistakes
- **Do not call APIs directly from components.** Create a `/api/` folder with one function per endpoint. This makes it easy to swap base URLs for staging vs production.
- **Do not store the Anthropic API key in the frontend.** It will be visible to anyone who opens DevTools. All LLM calls go through your backend.
- **Do not build the frontend before the APIs are tested.** You will spend hours debugging whether the bug is in the frontend or the backend. Test APIs in Postman/Swagger first.
- **Do not build all pages at once.** Build the critical path first: Dashboard → Rooms → New Booking → Invoice → Payment. Everything else can come after the demo.

### Deployment mistakes
- **Do not use the same database for development and production.** Seed data and test actions will corrupt production records.
- **Do not disable HTTPS.** Cloud Run handles this automatically — don't try to override it.
- **Do not set `--min-instances=1` without understanding the cost.** A single always-on Cloud Run instance costs ~$15–20/month. Fine at scale, but during free trial use min=0.
- **Do not forget to run migrations on the production database before deploying new backend code.**

### Scope mistakes
- **Do not add features during the demo build phase.** Finish the core loop first. The demo needs to show: book a room → check in → generate invoice → record payment. That's it.
- **Do not build a guest-facing booking website yet.** That's a V2 feature. This is a staff tool.
- **Do not integrate OTAs (Booking.com, MakeMyTrip) yet.** Complex, and not needed for demo.
- **Do not build multi-property support yet.** One property, done well, is the demo. Multi-property is a SaaS scaling feature.

---

## 11. DEMO SCRIPT (5 KEY SCENARIOS)

Walk through these with the client in order. Each takes ~3 minutes.

**Scenario 1 — New room booking**
New guest calls asking for a Deluxe room for 3 nights next week. Show: availability check, guest creation, booking confirmation, auto-generated invoice.

**Scenario 2 — Morning briefing**
Open the Dashboard at 7am. Show: today's check-ins, check-outs, one active event, any alerts (e.g. low linen stock). Manager Agent generates the summary.

**Scenario 3 — Wedding enquiry → event creation**
A couple calls for their 200-guest wedding. Show: lead creation, space availability check (Lawn A is free, Grand Hall is booked that day), event booking, quote PDF generation.

**Scenario 4 — Check-in + payment**
Guest arrives. Show: find booking by name, one-click check-in, WhatsApp notification sent to guest. Record partial payment (advance), show invoice updates to show balance due.

**Scenario 5 — Inventory alert**
Someone tries to book an event for 250 guests. Inventory Agent flags: only 220 chairs available. System suggests ordering rental chairs and shows the alert on the dashboard.

---

## 12. QUICK REFERENCE COMMANDS

```bash
# Start local development
docker-compose up -d            # Start PostgreSQL
cd backend
source venv/bin/activate
uvicorn app.main:app --reload   # Start backend on :8000

cd frontend
npm run dev                     # Start frontend on :5173

# Database
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1            # Undo last migration (careful in production)

# Reset dev database (destroys all data)
alembic downgrade base && alembic upgrade head && python seed.py

# View API docs
open http://localhost:8000/docs  # Swagger UI — test all endpoints here

# Docker
docker-compose logs -f backend   # Watch backend logs
docker-compose restart backend   # Restart after code changes (if not using --reload)

# GCP deploy (after setup)
gcloud builds submit --tag gcr.io/PROJECT_ID/pms-backend
gcloud run deploy pms-backend --image gcr.io/PROJECT_ID/pms-backend --region asia-south1
```

---

## 13. CONTACTS AND DECISIONS LOG

Use this section to track decisions made and questions resolved.

| Date | Decision | Reason |
|------|----------|--------|
| — | FastAPI over Django | Async performance, better for agent orchestration |
| — | PostgreSQL over MongoDB | Relational data, transactions critical for booking integrity |
| — | Cloud Run over App Engine | Pay per request, scales to zero, cheaper during development |
| — | Razorpay over Stripe | India-first, UPI support, easier KYC |
| — | React over Next.js | Internal tool, SSR not needed, simpler deployment |

---

*Document version: 1.0*
*Property Management System — Agentic Edition*
*Last updated: April 2026*
