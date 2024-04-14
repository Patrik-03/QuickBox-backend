import base64
import hashlib
import json
import re

import httpx
import psycopg2
from fastapi import APIRouter, WebSocket, HTTPException
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
    except (Exception, psycopg2.Error) as error:
        raise HTTPException(status_code=400, detail="User already exists")
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
    cursor2 = conn.cursor()
    try:
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.match(email_regex, email):
            raise HTTPException(status_code=400, detail="Invalid email")

        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        cursor.execute(f"""INSERT INTO quickbox.public.accounts (name, email, password, longitude, latitude) 
                            VALUES ('{name}', '{email}', '{hashed_password}', {longitude}, {latitude});""")
        conn.commit()
        cursor.close()
        cursor2.execute(f"""SELECT id, name, email, password, longitude, latitude
        FROM accounts 
        WHERE email = '{email}';""")
        record = cursor2.fetchone()
        cursor2.close()
        return {'id': record[0], 'name': record[1], 'email': record[2], 'password': record[3], 'longitude': record[4],
                'latitude': record[5]}

    except (Exception, psycopg2.Error) as error:
        raise HTTPException(status_code=400, detail=str(error))
    finally:
        conn.close()


@router.websocket("/ws/signup")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            message = await websocket.receive_text()
            data = json.loads(message)
            user_id = data.get('id')
            if not user_id:
                name_data = data.get('name')
                email_data = data.get('email')
                pass_data = data.get('password')
                longitude_data = data.get('longitude')
                latitude_data = data.get('latitude')
            else:
                qr_code_data = data.get('qr_code')
                qr_code_blob = base64.b64decode(qr_code_data)

            async with httpx.AsyncClient() as client:
                if user_id:
                    # Update existing account
                    response = await client.put(f"http://{settings.IP}:8000/update_qr",
                                                params={"user_id": user_id, "qr_code": qr_code_blob})

                else:
                    # Create new account
                    response = await client.post(f"http://{settings.IP}:8000/signup",
                                                 params={"name": name_data, "email": email_data, "password": pass_data,
                                                         "longitude": longitude_data, "latitude": latitude_data})

            await websocket.send_text(str(response.json()))

        except HTTPException as e:
            error_message = {"error": str(e.detail)}
            await websocket.send_text(json.dumps(error_message))
        except WebSocketDisconnect:
            break


@router.post("/signup")
async def signup(name: str, email: str, password: str, longitude: float, latitude: float):
    if checkUser(name):
        return createUser(name, email, password, longitude, latitude)
    else:
        raise HTTPException(status_code=400, detail="User already exists")


@router.put("/update_qr")
async def update_qr(user_id: int, qr_code: str):
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
        UPDATE accounts
        SET qr_code = '{qr_code}'
        WHERE id = {user_id};
        """)
        conn.commit()
        return {"status": "QR code updated successfully"}
    except (Exception, psycopg2.Error) as error:
        raise HTTPException(status_code=400, detail=str(error))
    finally:
        cursor.close()
        conn.close()