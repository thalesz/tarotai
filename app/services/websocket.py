from fastapi import WebSocket
from typing import Dict

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[user_id] = websocket

    def disconnect(self, user_id: str):
        self.connections.pop(user_id, None)

    async def send_notification(self, user_id: str, message: str, id_notification: int):
        ws = self.connections.get(user_id)
        # print(f"Sending notification to user {user_id}: {message}")
        if ws:
            try:
                await ws.send_json({"id": id_notification, "message": message})
            except Exception as e:
            # Optionally log the exception or handle it as needed
                self.disconnect(user_id)

# Instância global
ws_manager = WebSocketManager()
