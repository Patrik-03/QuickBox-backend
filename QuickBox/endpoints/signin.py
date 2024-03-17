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


@router.websocket("/ws/signin")  # Adjust the WebSocket endpoint path
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            email_data = data.get('signInEmail')
            pass_data = data.get('signInPassword')
            result_email = getUserEmail(email_data)
            result_pass = getUserPassword(pass_data)
            if result_email is True and result_pass is True:
                await websocket.send_text("true")
            else:
                await websocket.send_text("false")

    except ConnectionClosedError:
        await websocket.close()
