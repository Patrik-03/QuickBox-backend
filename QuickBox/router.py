from fastapi import APIRouter

from QuickBox.endpoints import signin
from QuickBox.endpoints import signup
from QuickBox.endpoints import home
from QuickBox.endpoints import deliveries
from QuickBox.endpoints import deliveries_history

router = APIRouter()
router.include_router(signin.router, tags=["signin"])
router.include_router(signup.router, tags=["signup"])
router.include_router(home.router, tags=["home"])
router.include_router(deliveries.router, tags=["deliveries"])
router.include_router(deliveries_history.router, tags=["deliveries_history"])
