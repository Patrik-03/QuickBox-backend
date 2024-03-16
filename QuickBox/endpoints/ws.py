import json

import psycopg2
from fastapi import APIRouter, WebSocket
from websockets.exceptions import ConnectionClosedError
from QuickBox.config import settings

router = APIRouter()


def getUserEmail(email: str):
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


def getUserPassword(password: str):
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    try:
        cursor.execute(f"""SELECT password FROM accounts WHERE password = '{password}';""")
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


@router.websocket("/ws")  # Adjust the WebSocket endpoint path
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            print(message)
            data = json.loads(message)
            data_type = data.get('type')
            data_content = data.get('content')
            if data_type == 'signInEmail':
                message = getUserEmail(data_content)
                if message:
                    await websocket.send_text(json.dumps({'type': data_type, 'content': 'true'}))
                else:
                    await websocket.send_text(json.dumps({'type': data_type, 'content': 'false'}))
            elif data_type == 'signInPassword':
                message = getUserPassword(data_content)
                if message:
                    await websocket.send_text(json.dumps({'type': data_type, 'data': 'true'}))
                else:
                    await websocket.send_text(json.dumps({'type': data_type, 'data': 'false'}))
    except ConnectionClosedError:
        await websocket.close()
