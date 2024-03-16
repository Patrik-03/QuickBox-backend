from fastapi import APIRouter

from QuickBox.endpoints import ws

router = APIRouter()
router.include_router(ws.router, tags=["statusv1"])
