import asyncio
import threading
import time

import httpx
from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2
from fastapi import APIRouter, HTTPException
from starlette.websockets import WebSocket

from QuickBox.config import settings
from QuickBox.endpoints.websocketmanager import WebSocketManager

router = APIRouter()


def get_package_location(delivery_id):
    location = ''
    current_latitude = ''
    current_longitude = ''
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
        cursor.execute(f"""SELECT accounts.longitude, accounts.latitude, deliveries.id
        FROM accounts 
        JOIN deliveries ON accounts.id = deliveries.from_id
        WHERE deliveries.id = {delivery_id};""")
        delivery = cursor.fetchone()
        conn.commit()
        cursor2.execute(f"SELECT latitude,longitude FROM deliveries WHERE id = {delivery_id};")
        delivery2 = cursor2.fetchone()
        conn.commit()
        cursor.close()
        cursor2.close()
        if not delivery:
            print(f"No delivery found with ID {delivery_id}")
            return
        if delivery2[0] is None and delivery2[1] is None:
            current_latitude = str(float(delivery[1]) + 0.01)
            current_longitude = delivery[0]

        elif float(delivery2[0]) <= float(delivery[1]) + 0.0001 and float(delivery2[1]) <= float(delivery[0]) + 0.0001:
            cursor5 = conn.cursor()
            cursor5.execute(f"UPDATE deliveries SET status = 'Delivered' WHERE id = {delivery_id};")
            conn.commit()
            cursor5.close()
            return None
        else:
            print(delivery2[0])
            current_latitude = str(float(delivery2[0]) - 0.001)
            current_longitude = delivery2[1]
        cursor3 = conn.cursor()
        print(current_latitude)
        cursor3.execute(f"""UPDATE deliveries 
                                    SET latitude = {current_latitude}, longitude = {current_longitude}
                                    WHERE id = {delivery_id};""")
        conn.commit()
        cursor3.close()
        cursor4 = conn.cursor()
        cursor4.execute(f"""SELECT * FROM deliveries WHERE id = {delivery_id};""")
        delivery = cursor4.fetchone()
        cursor4.close()
        conn.commit()
        conn.close()
        location = [{
            'id': delivery[0],
            'from': delivery[2],
            'sent_time': delivery[3],
            'delivery_time': delivery[4],
            'delivery_type': delivery[5],
            'status': delivery[6],
            'note': delivery[7],
            'latitude': delivery[8],
            'longitude': delivery[9]

        }]
    except Exception as e:
        print(f"Error getting delivery location: {e}")
    return {'items': location}


class LocationSimulator(threading.Thread):
    def __init__(self, delivery_id, websocket: WebSocket):
        super().__init__()
        self.delivery_id = delivery_id
        self.websocket = websocket
        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.is_set():
            location = get_package_location(self.delivery_id)
            if location:
                asyncio.run(self.send_location(location, self.websocket))
            else:
                self.stop_event.set()
            time.sleep(2)

    @router.websocket("/ws/deliveries")
    async def send_location(self, location, websocket: WebSocket):
        try:
            if websocket is None:
                return
            await websocket.send_text(str(location))
            print(f"Location sent: {str(location)}")
        except Exception as e:
            print(f"Error sending location: {e}")

    def stop(self):
        self.stop_event.set()


@router.put('/updateDelivery/{delivery_id}')
async def update_delivery(delivery_id: int):
    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    statuses = ['Sent', 'Received by courier', 'On the go', 'Nearby', 'Delivered']
    try:
        cursor.execute(f"SELECT * FROM deliveries WHERE id = {delivery_id};")
        delivery = cursor.fetchone()

        if not delivery:
            print(f"No delivery found with ID {delivery_id}")
            raise HTTPException(status_code=404, detail="Delivery not found")

        current_status = delivery[6]
        next_status = current_status
        simulator = LocationSimulator(delivery_id, WebSocketManager().get_websocket(int(delivery[1])+2))
        if current_status != statuses[-1]:
            next_status = statuses[statuses.index(current_status) + 1]
        if not simulator.is_alive():
            if next_status != 'Delivered':
                await WebSocketManager().send_message(
                    int(delivery[1])+1,
                    str({'type': 'delivery_status_update', 'delivery_id': delivery_id, 'status': next_status})
                )
            if current_status == 'Nearby':  # if current status is 'Nearby' then start simulations
                simulator.start()
            elif current_status != statuses[-1]:  # if current status is not 'delivered'
                # find the index of the current status in the list and set the status to the next one
                cursor.execute(f"UPDATE deliveries SET status = '{next_status}' WHERE id = {delivery_id};")
                conn.commit()
                print(f"Delivery with ID {delivery_id} updated successfully")

                return
            else:
                simulator.stop()
                await WebSocketManager().send_message(
                    1,
                    str({'type': 'delivery_status_update', 'delivery_id': delivery_id, 'status': next_status})
                )
                print(f"Delivery with ID {delivery_id} is already delivered")
                async with httpx.AsyncClient() as client:
                    response = await client.delete(f"http://{settings.IP}:8000/deleteDelivery/{delivery_id}",
                                                   params={"delivery_id": delivery[0],
                                                           "user_id": delivery[1],
                                                           "from_id": delivery[2],
                                                           "sent_time": delivery[3],
                                                           "delivery_time": delivery[4],
                                                           "delivery_type": delivery[5],
                                                           "status": delivery[6],
                                                           "note": delivery[7]})
                return {'status': 'delivered'}

    except (Exception, psycopg2.Error) as error:
        raise HTTPException(status_code=400, detail=str(error))
    finally:
        cursor.close()
        conn.close()


def run_in_new_loop(func, *args):
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    try:
        coroutine = func(*args)
        result = new_loop.run_until_complete(coroutine)
        if result == 'delivered':
            new_loop.stop()
        return result
    finally:
        new_loop.close()


def update_delivery_status(delivery_type: str, delivery_id: int, stop):
    scheduler = BackgroundScheduler()
    if delivery_type == 'economy':
        job = scheduler.add_job(run_in_new_loop, 'interval', minutes=1,
                                args=[update_delivery_call, delivery_id, stop, scheduler])
    elif delivery_type == 'standard':
        job = scheduler.add_job(run_in_new_loop, 'interval', seconds=30,
                                args=[update_delivery_call, delivery_id, stop, scheduler])
    elif delivery_type == 'fast':
        job = scheduler.add_job(run_in_new_loop, 'interval', seconds=10,
                                args=[update_delivery_call, delivery_id, stop, scheduler])
    job.modify(args=[update_delivery_call, delivery_id, stop, scheduler, job.id])  # Include the WebSocket argument
    scheduler.start()
    return job.id


async def update_delivery_call(delivery_id: int, stop, scheduler, job_id):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"http://{settings.IP}:8000/updateDelivery/{delivery_id}",
                                        params={"delivery_id": delivery_id})
            if response is not None and response.json() is not None:
                data = response.json()
                print(data)
                if data.get('status') == 'delivered':
                    stop.set()
                    scheduler.remove_job(job_id)
                    return 'delivered'
    except Exception as e:
        print(f"Error updating delivery with ID {delivery_id}: {e}")
    return None


@router.delete('/deleteDelivery/{delivery_id}')
async def delete_delivery(delivery_id: int, user_id: int, from_id: int, sent_time: str, delivery_time: str,
                          delivery_type: str, status: str, note: str):
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
            INSERT INTO history (id, user_id, from_id, sent_time, delivery_time, delivery_type, status, note)
            VALUES ({delivery_id}, {user_id}, {from_id}, '{sent_time}', '{delivery_time}', '{delivery_type}', '{status}', '{note}');
            """)
        conn.commit()
        print("Delivery added to history successfully")
    except Exception as e:
        print(f"Error adding delivery to history: {e}")
    cursor.close()
    conn.close()

    conn = psycopg2.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        database=settings.DATABASE_NAME,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD
    )
    cursor = conn.cursor()
    try:
        cursor.execute(f"DELETE FROM deliveries WHERE id = {delivery_id};")
        conn.commit()
        print(f"Delivery with ID {delivery_id} deleted successfully")
    except Exception as e:
        print(f"Error deleting delivery with ID {delivery_id}: {e}")
    cursor.close()
    conn.close()
