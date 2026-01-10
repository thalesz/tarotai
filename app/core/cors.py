from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.configs import settings


def _resolve_allowed_origins() -> List[str]:
    default_dev_origins = [
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://purple-island-07cb6510f.6.azurestaticapps.net",
    ]

    allowed_origins: List[str] = settings.CORS_ORIGINS or []

    # Support CSV in a single env value
    if len(allowed_origins) == 1 and "," in allowed_origins[0]:
        allowed_origins = [o.strip() for o in allowed_origins[0].split(",") if o.strip()]

    if settings.FRONTEND_URL and settings.FRONTEND_URL not in allowed_origins:
        allowed_origins.append(settings.FRONTEND_URL)

    if not allowed_origins:
        allowed_origins = default_dev_origins

    return allowed_origins


def configure_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_resolve_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
