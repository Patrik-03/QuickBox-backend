import json

import psycopg2
from fastapi import APIRouter, WebSocket, HTTPException, Request
import httpx
from starlette.websockets import WebSocketDisconnect
from QuickBox.config import settings

router = APIRouter()


def getUser(email: str):
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    try:
        cursor.execute(f"""SELECT email FROM accounts WHERE email = '{email}';""")
        record = cursor.fetchone()
        if record is None:
            return False
        else:
            return True
    except (Exception, psycopg2.Error) as error:
        return {'error': str(error)}
    finally:
        cursor.close()
        conn.close()


@router.websocket("/ws/home")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            email_data = data.get('signInEmail')
            pass_data = data.get('signInPassword')

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get("http://192.168.1.33:8000/home",
                                            params={"email": email_data, "password": pass_data})

            await websocket.send_text(str(response.json()))

    except WebSocketDisconnect:
        await websocket.close()


@router.get("/home")
async def signin(email: str, password: str):
    # Perform user authentication logic here
    result_email = getUser(email)
    if result_email:
        return {"result": "True"}
    else:
        return {"result": "False"}

