from fastapi import APIRouter
from app.api import auth,user, chat

api_router = APIRouter(prefix="/api")

api_router.include_router(chat.router)
api_router.include_router(user.router)
api_router.include_router(auth.router)
