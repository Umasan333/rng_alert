import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException

API_KEY = os.getenv("API_KEY", "change-me")

app = FastAPI()
clients = []

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.append(ws)
    print("client connected:", len(clients))

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if ws in clients:
            clients.remove(ws)
        print("client disconnected:", len(clients))

@app.post("/alarm")
async def alarm(x_api_key: str | None = Header(default=None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")

    dead_clients = []

    for ws in clients:
        try:
            await ws.send_json({"type": "alarm"})
        except Exception:
            dead_clients.append(ws)

    for ws in dead_clients:
        if ws in clients:
            clients.remove(ws)

    return {"ok": True, "clients": len(clients)}