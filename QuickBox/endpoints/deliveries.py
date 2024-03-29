import json
from typing import Optional

import psycopg2
from fastapi import APIRouter, WebSocket, HTTPException, Request
import httpx
from starlette.websockets import WebSocketDisconnect

from QuickBox.config import settings

router = APIRouter()


def getDeliveries(id: int, del_id: Optional[int] = None):
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    try:
        if del_id != 0:
            cursor.execute(f"""
            select * from deliveries
            where user_id = {id} and id = {del_id};
            """)
            record = cursor.fetchone()
            if record is None:
                return None
            else:
                return {
                    'from': record[2],
                    'sent_time': record[3],
                    'delivery_time': record[4],
                    'delivery_type': record[5],
                    'status': record[6],
                    'notes': record[7],
                }
        else:
            cursor.execute(f"""
            select * from deliveries
            where user_id = {id};
            """)
            records = cursor.fetchall()
            if records is None:
                return None
            else:
                items = []
                for record in records:
                    items.append({
                        'id': record[0],
                        'from': record[2],
                        'delivery_time': record[4],
                        'status': record[6],
                    })
                return {
                    'items': items
                }
    except (Exception, psycopg2.Error) as error:
        return {'error': str(error)}
    finally:
        cursor.close()
        conn.close()


@router.websocket("/ws/deliveries")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            message = await websocket.receive_text()
            data = json.loads(message)
            id_data = data.get('id')
            del_id = data.get('del_id')

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"http://{settings.IP}:8000/deliveries/{id_data}?del_id={del_id}",
                                            params={"id": id_data, "del_id": del_id})

            await websocket.send_text(str(response.json()))
        except WebSocketDisconnect:
            break


@router.get("/deliveries/{id}")
async def deliveries(id : int, del_id: Optional[int] = None):
    result = getDeliveries(id, del_id)
    if result:
        return result
