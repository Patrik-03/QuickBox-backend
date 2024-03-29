import asyncio

import httpx
from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2
from fastapi import APIRouter

from QuickBox.config import settings

router = APIRouter()


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
    statuses = ['sent', 'received by courier', 'on the go', 'nearby', 'delivered']
    try:
        cursor.execute(f"SELECT * FROM deliveries WHERE id = {delivery_id};")
        delivery = cursor.fetchone()

        if not delivery:
            print(f"No delivery found with ID {delivery_id}")
            return

        current_status = delivery[6]
        if current_status != statuses[-1]:  # if current status is not 'delivered'
            # find the index of the current status in the list and set the status to the next one
            next_status = statuses[statuses.index(current_status) + 1]
            cursor.execute(f"UPDATE deliveries SET status = '{next_status}' WHERE id = {delivery_id};")
            conn.commit()
            print(f"Delivery with ID {delivery_id} updated successfully")
            return {'status': next_status}
        else:
            print(f"Delivery with ID {delivery_id} is already delivered")
            return {'status': 'delivered'}

    except Exception as e:
        print(f"Error updating delivery with ID {delivery_id}: {e}")
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
    if delivery_type == 'economy':
        scheduler = BackgroundScheduler()
        scheduler.add_job(run_in_new_loop, 'interval', minutes=1,
                          args=[update_delivery_call, delivery_id, stop, scheduler])
        scheduler.start()
    elif delivery_type == 'standard':
        scheduler = BackgroundScheduler()
        scheduler.add_job(run_in_new_loop, 'interval', seconds=30,
                          args=[update_delivery_call, delivery_id, stop, scheduler])
        scheduler.start()
    elif delivery_type == 'fast':
        scheduler = BackgroundScheduler()
        scheduler.add_job(run_in_new_loop, 'interval', seconds=10,
                          args=[update_delivery_call, delivery_id, stop, scheduler])
        scheduler.start()


async def update_delivery_call(delivery_id: int, stop):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"http://{settings.IP}:8000/updateDelivery/{delivery_id}",
                                    params={"delivery_id": delivery_id})
        print(response.json())
        if response.json().get('status') == 'delivered':
            stop.set()

        return 'delivered'
