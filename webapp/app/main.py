from os import environ
import asyncio

import logging

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.websockets import WebSocket, WebSocketDisconnect
import aioredis

from fastapi.staticfiles import StaticFiles

import json


REDIS_HOSTNAME = environ.get("REDIS_HOSTNAME", "localhost")
REDIS_PORT = environ.get("REDIS_PORT", 6379)
REDIS_STREAM = environ.get("REDIS_STREAM", "mystream")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

html = f"""
<!DOCTYPE html>
<html>
    <head>
        <title>DLAB batch log</title>
        <link rel="stylesheet" href="static/bootstrap.css">
    </head>
    <body>
        <div class="container">
            <dic class="row">
                <div class="col-lg-1"></div>
                <div class="col-lg-10">
                    <h1>DLAB batch log</h1>
                    <div id="log_items">
                        <input class="search" placeholder="Search" />
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th><span class="sort" data-sort="timestamp">timestamp</span></td>
                                    <th><span class="sort" data-sort="message">message</span></td>
                                    <th><span class="sort" data-sort="status">status</span></td>
                                </tr>
                            </thead>
                            <tbody id="messages" class="list">
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="col-lg-1"></div>
            </div>
        </div>
        <script src="static/list.js"></script>
        <script>

            var options = {{
                valueNames: [ 'timestamp', 'message', 'status' ],
                item: `<tr>
                    <td class="timestamp"></td>
                    <td class="message"></td>
                    <td class="status"></td>
                </tr>`
            }};

            var values = [];

            var userList = new List('log_items', options, values);

            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {{

                var data = JSON.parse(event.data)

                for (let step = 0; step < data.length; step++) {{

                    var log_item = data[step]
                    var log_item_data = log_item[log_item.length - 1]

                    userList.add({{
                        timestamp: log_item_data.timestamp,
                        message: log_item_data.message,
                        status: log_item_data.status,
                    }}, prepend=true);

                }}

            }};
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await redis_connector(websocket)


async def redis_connector(
    websocket: WebSocket, redis_uri: str = f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}"
):

    stream_name = REDIS_STREAM.encode('utf-8')

    async def stream_producer(conn, ws: WebSocket):
        try:
            history = await conn.xrevrange(stream_name, count=10)
            await ws.send_text(json.dumps(history))

            while True:
                stream = await conn.xread([stream_name])
                await ws.send_text(json.dumps(stream))
        except Exception as exc:
            logger.error(exc)

    conn = await get_redis_pool()
    await stream_producer(conn, websocket)

async def get_redis_pool():
    return await aioredis.create_redis(f'redis://{REDIS_HOSTNAME}', encoding="utf-8")