import uvicorn
from fastapi import FastAPI

from QuickBox import config
from QuickBox.router import router

app = FastAPI(title="QuickBox")
app.include_router(router)

if __name__ == '__main__':
    uvicorn.run(app, host=config.ip_address, port=8000)
