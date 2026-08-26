from fastapi import FastAPI

from backend.app.api.v1 import router as v1_router
from backend.app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(v1_router)