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

            return
        else:
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
                print(response.json())
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
    # Update the job's arguments with the job ID
    job.modify(args=[update_delivery_call, delivery_id, stop, scheduler, job.id])
    scheduler.start()
    return job.id  # return the job ID


async def update_delivery_call(delivery_id: int, stop, scheduler, job_id):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"http://{settings.IP}:8000/updateDelivery/{delivery_id}",
                                    params={"delivery_id": delivery_id})
        if response is not None and response.json() is not None:
            print(response.json())
            if response.json().get('status') == 'delivered':
                stop.set()
                scheduler.remove_job(job_id)  # use the correct job ID
            return 'delivered'


@router.delete('/deleteDelivery/{delivery_id}')
async def delete_delivery(delivery_id: int, user_id: int, from_id: int, sent_time: str, delivery_time: str, delivery_type: str, status: str, note: str):
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
