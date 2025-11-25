# app/main.py
import asyncio
import pathlib
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pyobservability.monitor import Monitor
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Monitor UI")
root = pathlib.Path(__file__).parent
templates_dir = root / "templates"
static_dir = root / "static"
templates = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

monitor = Monitor(poll_interval=float(os.getenv("POLL_INTERVAL", 2)))

@app.get("/")
async def index(request: Request):
    # pass configured targets to the template so frontend can prebuild UI
    return templates.TemplateResponse("index.html", {"request": request, "targets": monitor.targets})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await monitor.start()
    q = monitor.subscribe()
    try:
        while True:
            payload = await q.get()
            # send as JSON text
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        monitor.unsubscribe(q)
    except Exception:
        monitor.unsubscribe(q)
        try:
            await websocket.close()
        except:
            pass
    await monitor.stop()
