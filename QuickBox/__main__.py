import uvicorn
from fastapi import FastAPI

from QuickBox.router import router

app = FastAPI(title="QuickBox")
app.include_router(router)

if __name__ == '__main__':
    uvicorn.run(app, host="192.168.1.41", port=8000)
