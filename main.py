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
        await self.send_message(f"*** Welcome user {user_id} ***\n", user_id)
        await self.broadcast(f"User {user_id} connected\n", user_id)

    def disconnect(self, user_id: int) -> None:
        """
        Remove connection
        """
        del self.active_connections[user_id]
        self.broadcast(f"User {user_id} disconnected\n", user_id)

    async def send_message(self, message: str, to_id: int, from_id: int|None = None) -> None:
        """
        1 to 1 msg
        """
        await self.active_connections[to_id].send_json({"msg":message, "from": from_id})

    async def broadcast(self, message: str, user_id: int) -> None:
        """
        Broadcast msg for all but the sender
        """
        for connection in list(map(lambda item: item[1], filter(lambda item: item[0]!=user_id ,self.active_connections.items()))):
            await self.send_message(message, int(connection.path_params['user_id']), user_id)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"msg": "Connection test OK!"}

@app.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int) -> None:
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data, user_id)
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await manager.broadcast(f"User {user_id} disconnected\n", user_id)