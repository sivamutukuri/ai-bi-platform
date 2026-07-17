"""Aggregate all v1 API routers into a single router."""
from fastapi import APIRouter

from app.api.routes import analysis, auth, datasets, reports

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(datasets.router)
api_router.include_router(analysis.router)
api_router.include_router(reports.router)
