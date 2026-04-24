from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

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


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.APP_ENV}


# Routers registered here as each phase is built
# from app.routers import bookings, guests, events, invoices, payments, inventory, availability, leads, reports, agent
# app.include_router(bookings.router, prefix="/api/v1")
# ... etc
