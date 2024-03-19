from fastapi import APIRouter

from QuickBox.endpoints import signin
from QuickBox.endpoints import signup
from QuickBox.endpoints import home

router = APIRouter()
router.include_router(signin.router, tags=["signin"])
router.include_router(signup.router, tags=["signup"])
router.include_router(home.router, tags=["home"])
