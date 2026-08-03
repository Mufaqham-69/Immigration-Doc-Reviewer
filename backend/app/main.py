import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, billing, cases, documents
from app.core.config import get_settings
from app.db.database import Base, engine

logging.basicConfig(level=logging.INFO)
settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(documents.router)
app.include_router(billing.router)


@app.on_event("startup")
def on_startup():
    # MVP: create tables directly. Once you have real users, switch to
    # Alembic migrations (`alembic upgrade head`) instead of this line.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.APP_NAME}
