import json

import httpx
import psycopg2
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

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
        cursor.execute(f"""SELECT name, email, password, longitude, latitude
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


def createUser(name: str, email: str, password: str, longitude: float, latitude: float):
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    try:
        cursor.execute(f"""INSERT INTO quickbox.public.accounts (name, email, password, longitude, latitude) 
                        VALUES ('{name}', '{email}', '{password}', {longitude}, {latitude});""")
        conn.commit()
        cursor.close()
        conn.close()
    except (Exception, psycopg2.Error) as error:
        # Log the error for debugging purposes
        print(f"Error occurred while inserting user: {error}")
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
        cursor.execute(f"""SELECT id, name, email, password, longitude, latitude
        FROM accounts 
        WHERE email = '{email}';""")
        record = cursor.fetchone()
        return {'id': record[0], 'name': record[1], 'email': record[2], 'password': record[3], 'longitude': record[4],
                'latitude': record[5]}
    except (Exception, psycopg2.Error) as error:
        return {'error': str(error)}
    finally:
        cursor.close()
        conn.close()


@router.websocket("/ws/signup")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            message = await websocket.receive_text()
            data = json.loads(message)
            name_data = data.get('name')
            email_data = data.get('email')
            pass_data = data.get('password')
            longitude_data = data.get('longitude')
            latitude_data = data.get('latitude')

            async with httpx.AsyncClient() as client:
                response = await client.post(f"http://{settings.IP}:8000/signup",
                                             params={"name": name_data, "email": email_data, "password": pass_data,
                                                     "longitude": longitude_data, "latitude": latitude_data})

            await websocket.send_text(str(response.json()))
        except WebSocketDisconnect:
            break


@router.post("/signup")
async def signup(name: str, email: str, password: str, longitude: float, latitude: float):
    if checkUser(name):
        return createUser(name, email, password, longitude, latitude)
    else:
        return False
