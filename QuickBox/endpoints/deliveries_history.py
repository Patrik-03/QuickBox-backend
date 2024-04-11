import json

import psycopg2
from fastapi import APIRouter, WebSocket, HTTPException, Request
import httpx
from starlette.websockets import WebSocketDisconnect

from QuickBox.config import settings

router = APIRouter()


def getDeliveries(id : int):
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
        where user_id = {id};
        """)
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        print(records)
        if not records:
            items = []
            items.append({
                'id': "0",
                'type': 'history'
            })
            return {
                'items': items
            }
        else:
            items = []
            for record in records:
                items.append({
                    'id': record[0],
                    'type': 'history',
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
        try:
            message = await websocket.receive_text()
            data = json.loads(message)
            id_data = data.get('id')
            type = data.get('type')
            if type == 'delete':
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.delete(f"http://{settings.IP}:8000/delete_history/{id_data}",
                                                params={"id": id_data})
                await websocket.send_text(str(response.json()))
            else:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"http://{settings.IP}:8000/deliveries_history/{id_data}",
                                                params={"id": id_data})
                print(response.json())
                await websocket.send_text(str(response.json()))

        except WebSocketDisconnect:
            break


@router.get("/deliveries_history/{id}")
async def getDel(id : int):
    result = getDeliveries(id)
    if result:
        return result


@router.delete("/delete_history/{id}")
async def deleteHis(id : int):
    result = deleteHistory(id)
    if result:
        return result


def deleteHistory(id : int):
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM history WHERE user_id = {id};")
        record = cursor.fetchone()
        if record is None:
            raise HTTPException(status_code=400, detail="User not found")
        else:
            conn.close()
            cursor.close()

        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM history WHERE user_id = {id};")
            conn.commit()
            items = [{
                'id': id,
                'type': 'delete'
            }]
            return {
                'items': items
            }
        except Exception as e:
            print(f"Error deleting history with ID {id}: {e}")

        finally:
            cursor.close()
            conn.close()
    except (Exception, psycopg2.Error) as error:
        return {'error': str(error)}