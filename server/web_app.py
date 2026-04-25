from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from config import WEB_HOST, WEB_PORT
from database import Database
from validation import RegistrationValidationError, validate_registration
from vision_ai import VisionAI
import time

try:
    import cv2
except ImportError:
    cv2 = None

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
_UNSET = object()
db = None
vision = None


def configure_services(database=_UNSET, vision_ai=_UNSET):
    global db, vision
    if database is not _UNSET:
        db = database
    if vision_ai is not _UNSET:
        vision = vision_ai


def get_vision():
    global vision
    if vision is None:
        vision = VisionAI()
    return vision


def get_db():
    global db
    if db is None:
        db = Database()
    return db

class UserRegRequest(BaseModel):
    name: str
    nfc_uid: str
    password: str
    face_encoding: Optional[str] = None # Base64 or similar if sent from client, but here we capture from server camera

def generate_frames():
    while True:
        current_vision = get_vision()
        if current_vision.camera_available and current_vision.camera:
            success, frame = current_vision.camera.read()
            if not success:
                time.sleep(0.1)
                continue
            if cv2 is None:
                time.sleep(1)
                continue
            else:
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            time.sleep(1)

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@app.post("/api/capture_face")
async def capture_face():
    encoding_bytes, message = get_vision().capture_face_encoding()
    if encoding_bytes:
        app.state.last_capture = encoding_bytes
        return {"success": True, "message": message}
    return {"success": False, "message": message}

@app.get("/users_page", response_class=HTMLResponse)
async def users_page(request: Request):
    return templates.TemplateResponse(request=request, name="users.html")

@app.get("/api/users")
async def get_users():
    users = get_db().get_all_users()
    return [{"id": u[0], "username": u[1], "nfc_uid": u[2]} for u in users]

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    if get_db().delete_user(user_id):
        return {"success": True, "message": "User deleted successfully."}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete user.")

@app.post("/api/register")
async def register_user(reg: UserRegRequest):
    try:
        username, nfc_uid, password = validate_registration(reg.name, reg.nfc_uid, reg.password)
    except RegistrationValidationError as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=400)

    face_encoding = getattr(app.state, 'last_capture', None)
    
    user_id = get_db().add_user(username, nfc_uid=nfc_uid, password=password, face_encoding=face_encoding)
    if user_id:
        if face_encoding: app.state.last_capture = None
        return {"success": True, "message": f"User {username} registered successfully (ID: {user_id})"}
    else:
        return JSONResponse(
            {"success": False, "message": "Failed to register user. (NFC UID might already exist)"},
            status_code=409,
        )

from fastapi.responses import Response

def logs_payload():
    database = get_db()
    return {
        "logs": database.get_recent_logs(limit=20),
        "alert": database.has_consecutive_failures(limit=3),
    }

@app.get("/api/logs")
async def get_api_logs():
    try:
        return logs_payload()
    except Exception as e:
        print(f"[WEB API] Failed to fetch logs: {e}")
        return {
            "logs": [{"id": 0, "timestamp": "-", "username": "Error", "method": "-", "status": "LOG_FETCH_ERROR", "has_snapshot": False}],
            "alert": False,
        }

@app.get("/logs")
async def get_logs():
    try:
        return logs_payload()["logs"]
    except Exception as e:
        print(f"[WEB API] Failed to fetch legacy logs: {e}")
        return [{"id": 0, "timestamp": "-", "username": "Error", "method": "-", "status": "LOG_FETCH_ERROR", "has_snapshot": False}]

@app.get("/api/logs/{log_id}/snapshot")
async def get_snapshot(log_id: int):
    snapshot_bytes = get_db().get_log_snapshot(log_id)
    if snapshot_bytes:
        return Response(content=snapshot_bytes, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Snapshot not found")

def start_web_server():
    import uvicorn
    import os
    
    cert_path = os.path.join(os.path.dirname(__file__), "cert.pem")
    key_path = os.path.join(os.path.dirname(__file__), "key.pem")
    
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print(f"Web UI started at https://{WEB_HOST}:{WEB_PORT}")
        uvicorn.run(app, host=WEB_HOST, port=WEB_PORT, ssl_keyfile=key_path, ssl_certfile=cert_path)
    else:
        print(f"Web UI started at http://{WEB_HOST}:{WEB_PORT}")
        uvicorn.run(app, host=WEB_HOST, port=WEB_PORT)
