from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import Base, SessionLocal, engine
from .deps import hash_password
from . import models
from .routers import auth, suppliers, invoices, mandates, agent, approvals, transactions, webhooks, payments


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if not db.query(models.User).filter_by(email=settings.demo_email).first():
            db.add(models.User(email=settings.demo_email, password_hash=hash_password(settings.demo_password)))
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="PayPilot Shield", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, suppliers, invoices, mandates, agent, approvals, transactions, webhooks, payments):
    app.include_router(r.router)


@app.get("/health")
def health():
    return {"ok": True, "paypal_mode": settings.paypal_mode}
