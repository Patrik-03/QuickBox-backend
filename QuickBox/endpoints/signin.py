import json

import psycopg2
from fastapi import APIRouter, WebSocket, HTTPException, Request
import httpx

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


@router.websocket("/ws/signin")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        data = json.loads(message)
        email_data = data.get('signInEmail')
        pass_data = data.get('signInPassword')
        if email_data == "close" and pass_data == "close":
            await websocket.close()
        else:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"http://{settings.IP}:8000/signin",
                                            params={"email": email_data, "password": pass_data})

            await websocket.send_text(str(response.json()))


@router.get("/signin")
async def signin(email: str, password: str):
    # Perform user authentication logic here
    result_email = getUserEmail(email)
    result_pass = getUserPassword(password)
    if result_email and result_pass:
        return {"result": "True"}
    else:
        return {"result": "False"}

