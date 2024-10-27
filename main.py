from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """
        Add connection to active_connections
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        await self.send_message(f"*** Welcome user {user_id} ***", user_id)

    def disconnect(self, user_id: int) -> None:
        """
        Remove connection
        """
        del self.active_connections[user_id]

    async def send_message(self, message: str, user_id: int) -> None:
        """
        1 to 1 msg
        """
        await self.active_connections[user_id].send_text(message)

    async def broadcast(self, message: str, user_id: int) -> None:
        """
        Broadcast msg for all but the sender
        """
        for connection in map(lambda item: item[1], filter(lambda item: item[0]!=user_id ,self.active_connections.items())):
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"msg": "Connection test OK!"}

@app.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int) -> None:
    await manager.connect(websocket, user_id)
    try:
        await manager.broadcast(f"User {user_id} connected", user_id)
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data, user_id)
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await manager.broadcast(f"User {user_id} disconnected", user_id)