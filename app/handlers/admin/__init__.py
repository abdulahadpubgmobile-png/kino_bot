from aiogram import Router
from app.handlers.admin.add_movie import router as add_movie_router
from app.handlers.admin.panel import router as panel_router
from app.handlers.admin.channels import router as channels_router

admin_router = Router()
admin_router.include_routers(add_movie_router, panel_router, channels_router)
