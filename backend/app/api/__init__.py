from fastapi import APIRouter
from app.api import auth,chat
from app.api import info

api_router = APIRouter(prefix="/api")

api_router.include_router(chat.router)
api_router.include_router(info.router)
api_router.include_router(auth.router)
