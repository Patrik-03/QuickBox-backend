import json

import psycopg2
from fastapi import APIRouter, WebSocket
import httpx
from starlette.websockets import WebSocketDisconnect

from QuickBox.config import settings
from QuickBox.endpoints.websocketmanager import WebSocketManager

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
        try:
            message = await websocket.receive_text()
            WebSocketManager().add_websocket(1, websocket)
            data = json.loads(message)
            id_data = data.get('id')
            del_id = data.get('del_id')

            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://{settings.IP}:8000/home",
                                            params={"id": id_data})

            async with httpx.AsyncClient(timeout=30.0) as client:
                response2 = await client.get(f"http://{settings.IP}:8000/deliveries/{id_data}?del_id={del_id}",
                                            params={"id": id_data, "del_id": del_id})

            await websocket.send_text(str(response.json()))
            await websocket.send_text(str(response2.json()))
        except WebSocketDisconnect:
            break


@router.get("/home")
async def signin(id: int):
    # Perform user authentication logic here
    result = getUser(id)
    if result:
        return result

