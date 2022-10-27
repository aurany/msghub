from os import environ
from secrets import choice
from redis import Redis
from time import sleep
import time
import random


STREAM = environ.get("REDIS_STREAM", "mystream")

MESSAGES = [
    "A file was loaded",
    "A file was edited",
    "A file was deleted",
    "A file was created",
    "A file was moved",
]

STATUSES = [
    "OK", "ERROR"
]


def connect_to_redis():
    hostname = environ.get("REDIS_HOSTNAME", "localhost")
    port = environ.get("REDIS_PORT", 6379)

    r = Redis(hostname, port, retry_on_timeout=True)
    return r


def send_data(redis_connection):
    count = 0
    while True:
        try:
            data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "message": random.choice(MESSAGES),
                "status": random.choice(STATUSES),
            }
            resp = redis_connection.xadd(STREAM, data)
            print(resp)
            count += 1

        except ConnectionError as e:
            print("ERROR REDIS CONNECTION: {}".format(e))

        sleep(random.random()*2.0)


if __name__ == "__main__":
    connection = connect_to_redis()
    send_data(connection)