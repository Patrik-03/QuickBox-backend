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
        if del_id != 0 and del_id != -1:
            cursor.execute(f"""
            select deliveries.id, accounts.name, deliveries.sent_time, deliveries.delivery_time, deliveries.status, deliveries.note
            from deliveries
            join accounts on deliveries.from_id = accounts.id
            where user_id = {id} and deliveries.id = {del_id}
            """)
            record = cursor.fetchone()
            if record is None:
                cursor.execute(f"""select * from history
                where user_id = {id} and id = {del_id};""")
                record = cursor.fetchone()
                if record is None:
                    return None
                else:
                    return {
                        'id': record[0],
                        'from': record[1],
                        'sent_time': record[2],
                        'delivery_time': record[3],
                        'status': record[4],
                        'note': record[5],
                    }
            else:
                return {
                    'id': record[0],
                    'from': record[1],
                    'sent_time': record[2],
                    'delivery_time': record[3],
                    'status': record[4],
                    'note': record[5],
                }

        elif del_id == -1:
            cursor.execute(f"""
            select deliveries.id, accounts.name, deliveries.sent_time, deliveries.delivery_time, deliveries.status, deliveries.note
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
                    })
                return {
                    'items': items
                }
        else:
            cursor.execute(f"""
            select deliveries.id, accounts.name, deliveries.sent_time, deliveries.delivery_time, deliveries.status, deliveries.note
            from deliveries
            join accounts on deliveries.from_id = accounts.id
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
                        'from': record[1],
                        'sent_time': record[2],
                        'delivery_time': record[3],
                        'status': record[4],
                        'note': record[5],
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
