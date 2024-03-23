import json

import httpx
import psycopg2
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from QuickBox import config
from QuickBox.config import settings

router = APIRouter()


def checkUser(email: str):
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    try:
        cursor.execute(f"""SELECT name, email, password, city, street, street_number 
        FROM accounts 
        WHERE email = '{email}';""")
        record = cursor.fetchone()
        if record is None:
            return True
        else:
            return False
    except (Exception, psycopg2.Error) as error:
        return {'error': str(error)}
    finally:
        cursor.close()
        conn.close()


def createUser(name: str, email: str, password: str, city: str, street: str, street_number: int):
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    try:
        cursor.execute(f"""INSERT INTO quickbox.public.accounts (name, email, password, city, street, street_number) 
                        VALUES ('{name}', '{email}', '{password}', '{city}', '{street}', '{street_number}');""")
        conn.commit()  # Commit the transaction
        cursor.close()
        conn.close()
        return True
    except (Exception, psycopg2.Error) as error:
        # Log the error for debugging purposes
        print(f"Error occurred while inserting user: {error}")
        return False


@router.websocket("/ws/signup")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        data = json.loads(message)
        name_data = data.get('name')
        email_data = data.get('email')
        pass_data = data.get('password')
        city_data = data.get('city')
        street_data = data.get('street')
        street_number_data = data.get('street_number')

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"http://{config.ip_address}:8000/signup",
                                         params={"name": name_data, "email": email_data, "password": pass_data,
                                               "city": city_data, "street": street_data, "street_number": street_number_data})

        await websocket.send_text(str(response.json()))


@router.post("/signup")
async def signup(name: str, email: str, password: str, city: str, street: str, street_number: int):
    if checkUser(name):
        if createUser(name, email, password, city, street, street_number):
            return {"result": "ok"}
    else:
        return {"result": "not ok"}
