import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException

API_KEY = os.getenv("API_KEY", "change-me")

app = FastAPI()
clients = []

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.append(ws)

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        clients.remove(ws)

@app.post("/alarm")
async def alarm(x_api_key: str | None = Header(default=None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401)

    for ws in clients:
        await ws.send_json({"type": "alarm"})

    return {"ok": True}