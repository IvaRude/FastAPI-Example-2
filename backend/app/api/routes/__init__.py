from fastapi import APIRouter

from backend.app.api.routes.cleanings import router as units_router

router = APIRouter()

router.include_router(units_router, prefix="/units", tags=["units"])
