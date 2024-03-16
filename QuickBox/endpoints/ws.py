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
            message = json.loads(message)  # Parse the JSON message
            message_type = message.get('type')
            data = message.get('data')
            data = json.loads(data)
            data_type = data.get('type')
            data_content = data.get('content')
            if message_type == 'GET':
                if data_type == 'signInEmail':
                    message = getUserEmail(data_content)
                    if message:
                        result = {'result': 'true'}
                        await websocket.send_text(json.dumps(result))
                    else:
                        result = {'result': 'false'}
                        await websocket.send_text(json.dumps(result))
                elif data_type == 'signInPassword':
                    message = getUserPassword(data_content)
                    if message:
                        result = {'result': 'true'}
                        await websocket.send_text(json.dumps(result))
                    else:
                        await websocket.send_text(json.dumps({'result': 'false'}))

            elif message_type == 'POST':
                message = {'error': 'Invalid message type'}
                await websocket.send_text(json.dumps(message))

            elif message_type == 'PUT':
                message = {'error': 'Invalid message type'}
                await websocket.send_text(json.dumps(message))

            elif message_type == 'DELETE':
                message = {'error': 'Invalid message type'}
                await websocket.send_text(json.dumps(message))

            else:
                message = {'error': 'Invalid message type'}
    except ConnectionClosedError:
        await websocket.close()
