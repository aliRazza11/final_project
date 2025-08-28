# app/core/config.py
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

def add_cors(app):
    """
    Configure Cross-Origin Resource Sharing (CORS) for the FastAPI app.

    This middleware allows the frontend (configured via FRONTEND_ORIGIN in settings)
    to communicate with the backend by permitting cross-origin requests.

    Args:
        app (FastAPI): The FastAPI application instance to apply the middleware to.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN],
        allow_credentials=True, 
        allow_methods=["*"],
        allow_headers=["*"],
    )