# For relative imports to work in Python 3.6
import os, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from http.client import HTTPResponse
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from models.payload import Credentials

app = FastAPI()

fake_db = {
    1: {"name": "aaa", "email": "aaa@aa.fr", "password": "pwd123", "user_id": 1},
    2: {"name": "bbb", "email": "bbb@bb.fr", "password": "pwd456", "user_id": 2},
}

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        """
        Add connection to active_connections
        """
        if self.isActiveConnexion(user_id):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        self.active_connections[user_id] = websocket
        await self.send_message(f"*** Welcome user {user_id} ***\n", user_id)
        await self.broadcast(f"User {user_id} connected\n", user_id)

    def isActiveConnexion(self, user_id: int) -> bool:
        return self.active_connections.get(user_id, False)

    async def disconnect(self, user_id: int) -> None:
        """
        Remove connection
        """
        del self.active_connections[user_id]

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

@app.post("/login")
async def login(data: Credentials):
    for user in fake_db.values():
        if user["name"] == data.username and user["password"] == data.password:
            if manager.isActiveConnexion(user["user_id"]):
                return {"status_code": 403, "status": "ko", "user_id": user["user_id"], "msg":f"User {user["user_id"]} already connected"}
            return {"status_code": 200, "status": "ok", "user_id": user["user_id"]}
    return {"status_code": 401, "status": "ko", "user_id": None, "msg":f"Incorrect credentials {data}"}


@app.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int) -> None:
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data, user_id)
    except WebSocketDisconnect:
        await manager.disconnect(user_id)
        await manager.broadcast(f"User {user_id} disconnected\n", user_id)
