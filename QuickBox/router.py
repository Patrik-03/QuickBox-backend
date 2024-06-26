from fastapi import APIRouter

from QuickBox.endpoints import signin
from QuickBox.endpoints import signup
from QuickBox.endpoints import home
from QuickBox.endpoints import deliveries
from QuickBox.endpoints import deliveries_history
from QuickBox.endpoints import create_delivery
from QuickBox.endpoints import updateDelivery
from QuickBox.endpoints import deliveries_map
from QuickBox.endpoints import websocketmanager


router = APIRouter()
router.include_router(signin.router, tags=["signin"])
router.include_router(signup.router, tags=["signup"])
router.include_router(home.router, tags=["home"])
router.include_router(deliveries.router, tags=["deliveries"])
router.include_router(deliveries_history.router, tags=["deliveries_history"])
router.include_router(create_delivery.router, tags=["create_delivery"])
router.include_router(updateDelivery.router, tags=["updateDelivery"])
router.include_router(websocketmanager.router, tags=["websocketmanager"])
router.include_router(deliveries_map.router, tags=["deliveries_map"])