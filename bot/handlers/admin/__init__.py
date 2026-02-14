"""Admin panel handlers."""

from aiogram import Router
from filters import AdminFilter

from .broadcast import router as broadcast_router
from .credits import router as credits_router
from .panel import router as panel_router
from .stats import router as stats_router
from .users import router as users_router
from .wavespeed import router as wavespeed_router

# Create admin router with admin filter
admin_router = Router(name="admin")
admin_router.message.filter(AdminFilter())
admin_router.callback_query.filter(AdminFilter())

admin_router.include_router(panel_router)
admin_router.include_router(stats_router)
admin_router.include_router(users_router)
admin_router.include_router(credits_router)
admin_router.include_router(broadcast_router)
admin_router.include_router(wavespeed_router)

__all__ = ["admin_router"]
