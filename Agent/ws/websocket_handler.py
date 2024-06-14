# ws/websocket_handler.py
import asyncio
import websockets
import json
import logging

connected_clients = set()

async def progress_update(websocket, path):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            pass
    finally:
        connected_clients.remove(websocket)

async def notify_clients(message):
    if connected_clients:
        await asyncio.gather(*[client.send(message) for client in connected_clients])

def send_progress_update(node_name, status):
    message = json.dumps({"node": node_name, "status": status})
    asyncio.run(notify_clients(message))

def node_wrapper(node_func, node_name, state, app_config):
    send_progress_update(node_name, "in_progress")
    result = node_func(state, app_config)
    send_progress_update(node_name, "completed")
    return result

async def start_websocket_server():
    server = None
    port = 6789
    while not server:
        try:
            server = await websockets.serve(progress_update, "0.0.0.0", port)
            logging.info(f"WebSocket server started on port {port}")
        except OSError as e:
            if e.errno == 98:
                logging.warning(f"Port {port} already in use. Trying next port.")
                port += 1
            else:
                raise
    return server

async def stop_websocket_server(server):
    logging.info("Stopping WebSocket server...")
    server.close()
    await server.wait_closed()
