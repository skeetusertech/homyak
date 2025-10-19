from .commands import router as commands_router
from .addvideo import router as addh_router
from .addr import router as addr_router
from .state import router as state_router
from .promo import router as promo_router

admin_routers = [promo_router, commands_router, addh_router, addr_router, state_router]