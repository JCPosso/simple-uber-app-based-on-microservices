#!/usr/bin/env python3
import os
import asyncio
import json
import logging
import sys

import aio_pika
import httpx
from aio_pika import ExchangeType

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('matching_worker')

RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672/')
DRIVERS_URL = os.getenv('DRIVERS_URL', 'http://drivers:8004')
RIDES_URL = os.getenv('RIDES_URL', 'http://rides:8003')


async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process(requeue=True):
        try:
            body = json.loads(message.body.decode())
            logger.info('Received event: %s', body)

            if body.get('type') != 'ride.requested':
                logger.info('Skipping event type %s', body.get('type'))
                return

            ride_id = body.get('rideId')
            if not ride_id:
                logger.warning('ride.requested without rideId')
                return

            async with httpx.AsyncClient(timeout=10.0) as client:
                # ask drivers service for available driver
                try:
                    r = await client.get(f"{DRIVERS_URL}/v1/drivers/available")
                except Exception:
                    logger.exception('failed to contact drivers service')
                    raise

                if r.status_code == 200:
                    driver = r.json()
                    driver_id = driver.get('driverId')
                    if not driver_id:
                        logger.warning('drivers service returned invalid driver object')
                        return

                    # assign driver to ride
                    assign_resp = await client.patch(f"{RIDES_URL}/v1/rides/{ride_id}/assign", json={"driverId": driver_id})
                    if assign_resp.status_code in (200, 201):
                        logger.info('Assigned driver %s to ride %s', driver_id, ride_id)
                        # mark driver as ON_TRIP
                        try:
                            await client.patch(f"{DRIVERS_URL}/v1/drivers/{driver_id}/status", json={"status": "ON_TRIP"})
                        except Exception:
                            logger.exception('failed to update driver status')
                    else:
                        logger.warning('Failed to assign ride: %s %s', assign_resp.status_code, assign_resp.text)

                elif r.status_code == 204:
                    logger.info('No available drivers for ride %s', ride_id)
                else:
                    logger.warning('drivers service returned %s', r.status_code)

        except json.JSONDecodeError:
            logger.exception('invalid json in message')
            raise
        except Exception:
            logger.exception('error processing message, it will be requeued')
            raise


async def main():
    logger.info('Connecting to RabbitMQ %s', RABBITMQ_URL)
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    exchange = await channel.declare_exchange('ride_events', ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue('matching_queue', durable=True)
    await queue.bind(exchange, routing_key='ride.requested')

    logger.info('Waiting for ride.requested events on matching_queue')
    await queue.consume(handle_message, no_ack=False)

    # keep running
    try:
        await asyncio.Future()
    finally:
        await connection.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Shutting down')