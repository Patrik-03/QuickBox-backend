import json

import psycopg2
from fastapi import APIRouter, WebSocket, HTTPException
import httpx
from starlette.websockets import WebSocketDisconnect

from QuickBox.config import settings

router = APIRouter()


def getUserSignIn(email: str, password: str):
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    try:
        cursor.execute(f"""SELECT id, email, password, longitude, latitude, accounts.name FROM accounts WHERE email = '{email}' and  password = '{password}';""")
        record = cursor.fetchone()
        return {'id': record[0], 'email': record[1], 'password': record[2], 'longitude': record[3], 'latitude': record[4], 'name': record[5]}
    except (Exception, psycopg2.Error):
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    finally:
        cursor.close()
        conn.close()


@router.websocket("/ws/signin")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            message = await websocket.receive_text()
            data = json.loads(message)
            email_data = data.get('signInEmail')
            pass_data = data.get('signInPassword')
            if email_data == "close" and pass_data == "close":
                await websocket.close()
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"http://{settings.IP}:8000/signin",
                                                params={"email": email_data, "password": pass_data})
                await websocket.send_text(str(response.json()))
        except HTTPException as e:
            # Handle incorrect credentials case
            error_message = {"error": "Incorrect credentials"}
            await websocket.send_text(json.dumps(error_message))
        except WebSocketDisconnect:
            break


@router.get("/signin")
async def signin(email: str, password: str):
    results = getUserSignIn(email, password)

    return results

