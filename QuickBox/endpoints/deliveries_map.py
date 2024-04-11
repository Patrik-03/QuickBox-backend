import json

import psycopg2
from fastapi import APIRouter, WebSocket
import httpx
from starlette.websockets import WebSocketDisconnect

from QuickBox.config import settings
from QuickBox.endpoints.websocketmanager import WebSocketManager

router = APIRouter()


def getDeliveries(id: int):
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
                    select deliveries.id, accounts.name, deliveries.sent_time, deliveries.delivery_time, deliveries.status, deliveries.note, deliveries.latitude, deliveries.longitude
                    from deliveries
                    join accounts on deliveries.from_id = accounts.id
                    where user_id = {id} and deliveries.status = 'Nearby';
                    """)
        items = []
        records = cursor.fetchall()
        if records is None:
            return items
        else:
            for record in records:
                items.append({
                    'id': record[0],
                    'from': record[1],
                    'sent_time': record[2],
                    'delivery_time': record[3],
                    'status': record[4],
                    'note': record[5],
                    'latitude': record[6],
                    'longitude': record[7]
                })
            return {
                'items': items
            }
    except (Exception, psycopg2.Error) as error:
        return {'error': str(error)}
    finally:
        cursor.close()
        conn.close()


@router.websocket("/ws/deliveries_map")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            WebSocketManager().add_websocket(2, websocket)
            message = await websocket.receive_text()
            data = json.loads(message)
            id_data = data.get('id')
            del_id = data.get('del_id')

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"http://{settings.IP}:8000/deliveries_map/{id_data}",
                                            params={"id": id_data})

            await websocket.send_text(str(response.json()))
        except WebSocketDisconnect:
            break


@router.get("/deliveries_map/{id}")
async def deliveries(id : int):
    result = getDeliveries(id)
    if result:
        return result
