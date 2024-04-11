from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class WebSocketManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.websockets = {}
        return cls._instance

    def add_websocket(self, key, websocket):
        self.websockets[key] = websocket

    def get_websocket(self, key):
        return self.websockets.get(key)

    def remove_websocket(self, key):
        del self.websockets[key]

    async def send_message(self, key, message):
        websocket = self.get_websocket(key)
        if websocket:
            await websocket.send_text(message)
        else:
            print(f"No WebSocket found for key: {key}")
