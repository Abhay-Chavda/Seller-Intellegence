from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.db import Base, engine

from .routes import router

settings = get_settings()

app = FastAPI(
    title="Seller Intelligence Tools API",
    version="1.0.0",
    description="Dedicated tools-only API for Azure Foundry integration.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "tools_api"}


@app.get("/")
def root():
    return RedirectResponse(url="/docs")
