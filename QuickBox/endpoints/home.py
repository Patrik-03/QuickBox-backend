import json

import psycopg2
from fastapi import APIRouter, WebSocket, HTTPException, Request
import httpx

from QuickBox import config
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
        cursor.execute(f"""SELECT name, qr_code FROM accounts WHERE email = '{email}';""")
        record = cursor.fetchone()
        if record is None:
            return None
        else:
            return {'name': record[0], 'qr_code': record[1]}
    except (Exception, psycopg2.Error) as error:
        return {'error': str(error)}
    finally:
        cursor.close()
        conn.close()


@router.websocket("/ws/home")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        data = json.loads(message)
        email_data = data.get('email')

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"http://{config.ip_address}:8000/home",
                                        params={"email": email_data})

        await websocket.send_text(str(response.json()))


@router.get("/home")
async def signin(email: str):
    # Perform user authentication logic here
    result = getUser(email)
    if result:
        return result

