import logging
import os
import time
import random

import pika
import pika.channel
import pika.spec

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

amqp_url = os.environ['AMQP_URL'] if 'AMQP_URL' in os.environ else 'amqp://guest:guest@localhost:5672/%2F'
min = float(os.environ['SLEEP_MIN']) if 'SLEEP_MIN' in os.environ else 1.0
max = float(os.environ['SLEEP_MAX']) if 'SLEEP_MAX' in os.environ else 3.0


def on_message(channel: pika.channel.Channel, method: pika.spec.Basic.Deliver, _properties: pika.spec.BasicProperties, body: bytes):
    # pretend to work
    sleep_time = round(random.uniform(min, max), 1)
    LOGGER.info(
        f'Task received [{body.decode()}]. Sleeping for {sleep_time} seconds.')
    time.sleep(sleep_time)
    channel.basic_ack(delivery_tag=method.delivery_tag)


def main():
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    connection = pika.BlockingConnection(pika.URLParameters(amqp_url))

    channel = connection.channel()
    channel.basic_qos(prefetch_count=1)
    channel.queue_declare(queue='tasks')
    channel.basic_consume(queue='tasks', on_message_callback=on_message)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()


if __name__ == '__main__':
    main()
