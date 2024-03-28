import json
import time

import psycopg2
from fastapi import APIRouter, WebSocket, HTTPException, Request
import httpx

from QuickBox.config import settings

router = APIRouter()


def createDeliveries(user_id: int, from_id: int, sent_time: str, delivery_time: str, delivery_type: str, status: str, note: str):
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
        INSERT INTO deliveries (user_id, from_id, sent_time, delivery_time, delivery_type, status, note)
        VALUES ('{user_id}', '{from_id}', '{sent_time}', '{delivery_time}', '{delivery_type}', '{status}', '{note}');
        """)
        records = cursor.fetchall()
        cursor.close()
        conn.close()

    except (Exception, psycopg2.Error) as error:
        return {'error': str(error)}

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
        select * from deliveries
        where user_id = {user_id} and from_id = {from_id} and sent_time = '{sent_time}' and delivery_time = '{delivery_time}' and delivery_type = '{delivery_type}' and status = '{status}' and note = '{note}';
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
                'note': record[7],
            }
    finally:
        cursor.close()
        conn.close()


@router.websocket("/ws/create_deliveries")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        data = json.loads(message)
        user_id = data.get('receiveID')
        from_id = data.get('fromID')
        sent_time = time.strftime('%Y-%m-%d %H:%M:%S')
        delivery_type = data.get('deliveryType')
        delivery_time = ''
        if delivery_type == 'economy':
            delivery_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + 60 * 60 * 24 * 3))  # 3 days
        elif delivery_type == 'standard':
            delivery_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + 60 * 60 * 24 * 2))  # 2 days
        elif delivery_type == 'fast':
            delivery_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + 60 * 60 * 24 * 1))  # 1 day
        status = 'sent'
        note = data.get('note')

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"http://{settings.IP}:8000/create_deliveries",
                                        params={"user_id": user_id, "from_id": from_id, "sent_time": sent_time,
                                                "delivery_time": delivery_time, "delivery_type": delivery_type,
                                                "status": status, "note": note})

        await websocket.send_text(str(response.json()))


@router.get("/create_deliveries")
async def deliveriesC(user_id: int, from_id: int, sent_time: str, delivery_time: str, delivery_type: str, status: str,
                      note: str):
    return createDeliveries(user_id, from_id, sent_time, delivery_time, delivery_type, status, note)

