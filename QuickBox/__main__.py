import uvicorn
from fastapi import FastAPI

from QuickBox.config import settings
from QuickBox.router import router

app = FastAPI(title="QuickBox")
app.include_router(router)

if __name__ == '__main__':
    uvicorn.run(app, host=settings.IP, port=8000)
