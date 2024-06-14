# ws/websocket_handler.py
from flask_socketio import SocketIO, send, emit

socketio = SocketIO()

connected_clients = set()

@socketio.on('connect')
def handle_connect():
    connected_clients.add(request.sid)
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    connected_clients.remove(request.sid)
    print(f"Client disconnected: {request.sid}")

@socketio.on('message')
def handle_message(message):
    print(f"Received message: {message}")

def notify_clients(message):
    emit('message', message, broadcast=True)

def send_progress_update(node_name, status):
    message = {"node": node_name, "status": status}
    notify_clients(message)
