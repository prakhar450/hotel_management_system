from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import availability, guests, bookings, events, invoices, inventory, leads, reports, agent

app = FastAPI(
    title="PMS — Agentic Property Management System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(availability.router)
app.include_router(guests.router)
app.include_router(bookings.router)
app.include_router(events.router)
app.include_router(invoices.router)
app.include_router(inventory.router)
app.include_router(leads.router)
app.include_router(reports.router)
app.include_router(agent.router)


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.APP_ENV}
