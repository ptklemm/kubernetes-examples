import os
import logging
import sys
import json
from datetime import datetime
import time
from urllib.request import urlopen, Request
from http.client import HTTPResponse
from base64 import b64encode

from pika.adapters.blocking_connection import BlockingConnection, BlockingChannel
from pika.connection import URLParameters
from pika.spec import BasicProperties
from pika.delivery_mode import DeliveryMode

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)


def basic_auth(username, password):
    token = b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
    return f'Basic {token}'


def display_help():
    print('Valid commands are: ')
    print('    status: Display status of task queue.')
    print('    publish [number]: Publish the specified number of messages. If no number is specified, then 100 messages are published.')


def display_status():
    username = "guest"
    password = "guest"
    url = "http://localhost:15672/api/queues/%2F/tasks"

    response: HTTPResponse = urlopen(
        Request(method='GET', url=url, headers={'Authorization': basic_auth(username, password)}))

    data = json.loads(response.read())
    print("Status of 'tasks' queue: ")
    print(f"Messages: {data['messages']}")
    print(f"Consumers: {data['consumers']}")
    print(f"Consumer Capacity: {round(data['consumer_capacity']*100, 1)}%")
    print(
        f"Consumption Rate: {data['message_stats']['ack_details']['rate']} msgs/sec")


def publish_messages(argv: list[str]):
    connection = _connectAMQP()
    channel = connection.channel()
    channel.queue_declare('tasks')

    iterations = int(argv[2]) if len(argv) > 2 else 100
    for i in range(1, iterations+1):
        _publishAMQP(channel, str(i))

    connection.close()
    print(f'Published {iterations} messages.')


def generate_messages(argv: list[str]):
    connection = _connectAMQP()
    channel = connection.channel()
    channel.queue_declare('tasks')

    body = str()
    rate = float(argv[2]) if len(argv) > 2 else 1.0
    while True:
        body = datetime.utcnow().strftime(
            '%Y-%m-%d %H:%M:%S.%f')[:-3]
        _publishAMQP(channel, body)
        LOGGER.info(f'Published {body}')
        time.sleep(rate)


def _connectAMQP() -> BlockingConnection:
    amqp_url = 'amqp://guest:guest@localhost:5672/%2F'
    if 'AMQP_URL' in os.environ:
        amqp_url = os.environ['AMQP_URL']

    connection = None
    try:
        connection = BlockingConnection(URLParameters(amqp_url))
    except RuntimeError as error:
        raise error

    return connection


def _publishAMQP(channel: BlockingChannel, body: str):
    channel.basic_publish(exchange='',
                          routing_key='tasks',
                          body=body,
                          properties=BasicProperties(content_type='text/plain',
                                                     delivery_mode=DeliveryMode.Transient))


def main(argv: list[str]):
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    command = argv[1] if len(argv) > 1 else 'help'

    if command == 'help':
        display_help()
    elif command == 'status':
        display_status()
    elif command == 'publish':
        publish_messages(argv)
    elif command == 'generate':
        generate_messages(argv)
    else:
        print('Invalid command')
        display_help()


if __name__ == '__main__':
    main(sys.argv)
