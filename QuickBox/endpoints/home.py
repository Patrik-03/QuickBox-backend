import json

import psycopg2
from fastapi import APIRouter, WebSocket, HTTPException, Request
import httpx

from QuickBox.config import settings

router = APIRouter()


def getUser(id: int):
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    try:
        cursor.execute(f"""SELECT id, name FROM accounts WHERE id = '{id}';""")
        record = cursor.fetchone()
        if record is None:
            return None
        else:
            return {'id': record[0], 'name': record[1]}
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
        id_data = data.get('id')

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"http://{settings.IP}:8000/home",
                                        params={"id": id_data})

        async with httpx.AsyncClient(timeout=30.0) as client:
            response2 = await client.get(f"http://{settings.IP}:8000/deliveries",
                                        params={"id": id_data})

        await websocket.send_text(str(response.json()))
        await websocket.send_text(str(response2.json()))


@router.get("/home")
async def home(id: int):
    result = getUser(id)
    if result:
        return result

