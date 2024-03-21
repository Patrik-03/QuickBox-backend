import json

import psycopg2
from fastapi import APIRouter, WebSocket, HTTPException, Request
import httpx

from QuickBox import config
from QuickBox.config import settings

router = APIRouter()


def getDeliveries(email: str):
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
        select * from history
        join accounts a on history.user_id = a.id
        where a.email = '{email}';
        """)
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        if records is None:
            return None
        else:
            items = []
            for record in records:
                items.append({
                    'from': record[2],
                    'sent_time': record[3],
                    'delivery_time': record[4],
                    'delivery_type': record[5],
                    'status': record[6],
                    'notes': record[7],
                })
            return {
                'items': items
            }
    except (Exception, psycopg2.Error) as error:
        return {'error': str(error)}
    finally:
        cursor.close()
        conn.close()


@router.websocket("/ws/deliveries_history")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        data = json.loads(message)
        email_data = data.get('email')

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"http://{config.ip_address}:8000/deliveries_history",
                                        params={"email": email_data})

        await websocket.send_text(str(response.json()))


@router.get("/deliveries_history")
async def signin(email: str):
    # Perform user authentication logic here
    result = getDeliveries(email)
    if result:
        return result

