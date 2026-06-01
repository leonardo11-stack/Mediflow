from fastapi import APIRouter

from app.api.v1.endpoints import triagem

api_router = APIRouter()
api_router.include_router(triagem.router, tags=["triagem"])
