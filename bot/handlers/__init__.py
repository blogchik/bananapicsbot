from .generation import router as generation_router
from .profile import router as profile_router
from .start import router as start_router

__all__ = ["start_router", "profile_router", "generation_router"]
