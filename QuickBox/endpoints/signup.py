import json

import httpx
import psycopg2
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
from QuickBox.config import settings

router = APIRouter()


def checkUser(name: str, email: str, password: str, city: str, street: str, street_number: int, qr_code: str):
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    try:
        #find if there is a user with the same credentials
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


def createUser(name: str, email: str, password: str, city: str, street: str, street_number: int, qr_code: str):
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    try:
        cursor.execute(f"""INSERT INTO quickbox.public.accounts (name, email, password, city, street, street_number, qr_code) 
                        VALUES ('{name}', '{email}', '{password}', '{city}', '{street}', '{street_number}', '{qr_code}');""")
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
    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            name_data = data.get('name')
            email_data = data.get('email')
            pass_data = data.get('password')
            city_data = data.get('city')
            street_data = data.get('street')
            street_number_data = data.get('street_number')
            qr_code_data = data.get('qr_code')

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post("http://192.168.1.33:8000/signup",
                                             params={"name": name_data, "email": email_data, "password": pass_data,
                                                   "city": city_data, "street": street_data, "street_number": street_number_data, "qr_code": qr_code_data})

            await websocket.send_text(str(response.json()))

    except WebSocketDisconnect:
        await websocket.close()


@router.post("/signup")
async def signup(name: str, email: str, password: str, city: str, street: str, street_number: int, qr_code: str):
    if checkUser(name, email, password, city, street, street_number, qr_code):
        if createUser(name, email, password, city, street, street_number, qr_code):
            return {"result": "ok"}
    else:
        return {"result": "not ok"}
