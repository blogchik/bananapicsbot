from .generation import router as generation_router
from .admin import router as admin_router
from .payments import router as payments_router
from .profile import router as profile_router
from .referral import router as referral_router
from .start import router as start_router

__all__ = [
    "start_router",
    "profile_router",
    "payments_router",
    "referral_router",
    "admin_router",
    "generation_router",
]
