from fastapi import APIRouter

from QuickBox.endpoints import signin

router = APIRouter()
router.include_router(signin.router, tags=["signin"])
