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
cmd_callback = None
doorlock_server = None


def configure_services(database=_UNSET, vision_ai=_UNSET, command_callback=_UNSET, doorlock_server=_UNSET):
    global db, vision, cmd_callback
    if database is not _UNSET:
        db = database
    if vision_ai is not _UNSET:
        vision = vision_ai
    if command_callback is not _UNSET:
        cmd_callback = command_callback
    if doorlock_server is not _UNSET:
        globals()["doorlock_server"] = doorlock_server


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
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    face_encoding: Optional[str] = None # Base64 or similar if sent from client, but here we capture from server camera

def generate_frames():
    """MJPEG 스트림. 카메라 없거나 mock 모드면 깔끔한 플레이스홀더를 보여준다."""
    placeholder = None
    last_placeholder_time = 0

    def _make_placeholder():
        if cv2 is None:
            # 1x1 black JPEG fallback (매우 작은 데이터)
            return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\x22 "\x1c\x1c(7+2\'\x1c\x1c1=81(.?\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\x1c\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xbf\xff\xd9'
        import numpy as np
        h, w = 360, 640
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        try:
            from PIL import Image, ImageDraw, ImageFont
            image = Image.new("RGB", (w, h), (15, 23, 42))
            draw = ImageDraw.Draw(image)
            for y in range(h):
                shade = int(42 + (y / h) * 28)
                draw.line((0, y, w, y), fill=(15, 23, shade))
            draw.rectangle((0, 0, w - 1, h - 1), outline=(51, 65, 85), width=2)
            draw.rounded_rectangle((222, 70, 418, 118), radius=10, fill=(30, 41, 59), outline=(71, 85, 105), width=1)
            draw.ellipse((244, 86, 258, 100), fill=(239, 68, 68))
            font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
            title_font = ImageFont.truetype(font_path, 34)
            body_font = ImageFont.truetype(font_path, 20)
            small_font = ImageFont.truetype(font_path, 15)
            mono_font = ImageFont.truetype(font_path, 14)
            draw.text((266, 82), "OFFLINE", font=mono_font, fill=(226, 232, 240))
            draw.text((212, 145), "카메라 연결 대기", font=title_font, fill=(248, 250, 252))
            draw.text((160, 198), "ESP32-CAM USB-C 연결 후 재시도하세요", font=body_font, fill=(203, 213, 225))
            draw.line((170, 250, 470, 250), fill=(71, 85, 105), width=1)
            draw.text((230, 278), "2FA Smart Doorlock", font=small_font, fill=(148, 163, 184))
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        except Exception:
            frame[:] = (42, 23, 15)
            cv2.putText(frame, "CAMERA OFFLINE", (160, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (245, 245, 245), 2)
            cv2.putText(frame, "ESP32-CAM USB-C required", (145, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        return cv2.imencode('.jpg', frame)[1].tobytes()

    while True:
        current_vision = get_vision()
        if current_vision.camera_available and current_vision.camera:
            success, frame = current_vision.camera.read()
            if success and cv2 is not None:
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                    time.sleep(0.05)
                    continue
        # 카메라 없음 / mock → 플레이스홀더 (1초에 한 번만 새로 그림)
        now = time.time()
        if placeholder is None or now - last_placeholder_time > 1.0:
            placeholder = _make_placeholder()
            last_placeholder_time = now
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
        time.sleep(0.8)

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@app.get("/logs_page", response_class=HTMLResponse)
async def logs_page(request: Request):
    return templates.TemplateResponse(request=request, name="logs.html")

@app.get("/hardware", response_class=HTMLResponse)
async def hardware_page(request: Request):
    return templates.TemplateResponse(request=request, name="hardware.html")

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
    payload = []
    database = get_db()
    for user in users:
        activity = database.get_user_activity(user[0], limit=3)
        payload.append({
            "id": user["id"],
            "username": user["username"],
            "nfc_uid": user["nfc_uid"],
            "email": user["email"],
            "phone": user["phone"],
            "address": user["address"],
            "member_uuid": user["member_uuid"],
            "face_enrolled": bool(user["face_enrolled"]),
            "stats": activity["stats"] if activity else {},
        })
    return payload

@app.get("/api/users/{user_id}/activity")
async def get_user_activity(user_id: int, limit: int = 50):
    activity = get_db().get_user_activity(user_id, limit=limit)
    if not activity:
        raise HTTPException(status_code=404, detail="User not found.")
    return activity

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
    
    user_id = get_db().add_user(
        username,
        nfc_uid=nfc_uid,
        password=password,
        face_encoding=face_encoding,
        email=(reg.email or "").strip() or None,
        phone=(reg.phone or "").strip() or None,
        address=(reg.address or "").strip() or None,
    )
    if user_id:
        if face_encoding: app.state.last_capture = None
        return {"success": True, "message": f"User {username} registered successfully (ID: {user_id})"}
    else:
        return JSONResponse(
            {"success": False, "message": "Failed to register user. (NFC UID might already exist)"},
            status_code=409,
        )

from fastapi.responses import Response

def logs_payload(limit=20, offset=0):
    database = get_db()
    data = database.get_logs(limit=limit, offset=offset)
    return {
        "logs": data["logs"],
        "total": data["total"],
        "limit": data["limit"],
        "offset": data["offset"],
        "alert": database.has_consecutive_failures(limit=3),
    }


def _camera_status():
    current_vision = get_vision()
    if hasattr(current_vision, "get_status"):
        return current_vision.get_status()
    return {
        "connected": False,
        "status": "unavailable",
        "mock": False,
        "source": "unknown",
        "backend": current_vision.__class__.__name__,
        "port": None,
        "last_error": "Vision service does not expose status.",
        "candidates": [],
    }


def _arduino_status():
    if doorlock_server and hasattr(doorlock_server, "get_serial_status"):
        return doorlock_server.get_serial_status()
    return {
        "connected": False,
        "status": "unavailable",
        "port": None,
        "configured_port": None,
        "baud_rate": None,
        "last_error": "DoorLockServer is not configured.",
        "candidates": [],
        "last_probe_at": None,
    }


def status_payload():
    return {
        "arduino": _arduino_status(),
        "camera": _camera_status(),
        "server_time": time.time(),
    }

@app.get("/api/logs")
async def get_api_logs(limit: int = 20, offset: int = 0):
    try:
        return logs_payload(limit=limit, offset=offset)
    except Exception as e:
        print(f"[WEB API] Failed to fetch logs: {e}")
        return {
            "logs": [{"id": 0, "timestamp": "-", "username": "Error", "method": "-", "status": "LOG_FETCH_ERROR", "has_snapshot": False}],
            "total": 1,
            "limit": limit,
            "offset": offset,
            "alert": False,
        }

@app.post("/api/demo/seed")
async def seed_demo_data():
    return {"success": True, "users": get_db().seed_demo_data()}


@app.get("/api/status")
async def get_api_status():
    return status_payload()


@app.post("/api/reconnect/arduino")
async def reconnect_arduino():
    if not doorlock_server or not hasattr(doorlock_server, "reconnect_serial"):
        raise HTTPException(status_code=500, detail="DoorLockServer is not configured.")
    ok = doorlock_server.reconnect_serial()
    return {
        "success": bool(ok),
        "message": "Arduino reconnected." if ok else "Arduino reconnect failed.",
        "status": status_payload(),
    }


@app.post("/api/reconnect/camera")
async def reconnect_camera():
    current_vision = get_vision()
    if not hasattr(current_vision, "reconnect"):
        raise HTTPException(status_code=500, detail="Vision service does not support reconnect.")
    ok = current_vision.reconnect()
    return {
        "success": bool(ok),
        "message": "Camera reconnected." if ok else "Camera reconnect failed.",
        "status": status_payload(),
    }


@app.post("/api/reconnect/all")
async def reconnect_all():
    arduino_ok = False
    camera_ok = False

    if doorlock_server and hasattr(doorlock_server, "reconnect_serial"):
        arduino_ok = bool(doorlock_server.reconnect_serial())

    current_vision = get_vision()
    if hasattr(current_vision, "reconnect"):
        camera_ok = bool(current_vision.reconnect())

    return {
        "success": arduino_ok and camera_ok,
        "message": "Reconnect completed.",
        "arduino_success": arduino_ok,
        "camera_success": camera_ok,
        "status": status_payload(),
    }

@app.get("/logs")
async def get_logs():
    try:
        return logs_payload(limit=100)["logs"]
    except Exception as e:
        print(f"[WEB API] Failed to fetch legacy logs: {e}")
        return [{"id": 0, "timestamp": "-", "username": "Error", "method": "-", "status": "LOG_FETCH_ERROR", "has_snapshot": False}]

@app.get("/api/logs/{log_id}/snapshot")
async def get_snapshot(log_id: int):
    snapshot_bytes = get_db().get_log_snapshot(log_id)
    if snapshot_bytes:
        return Response(content=snapshot_bytes, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Snapshot not found")

@app.post("/api/control/open")
async def control_open_door():
    if cmd_callback:
        cmd_callback("OPEN_DOOR")
        return {"success": True, "message": "Door open command sent."}
    raise HTTPException(status_code=500, detail="Command callback not configured.")

@app.post("/api/control/lockdown")
async def control_lockdown():
    if cmd_callback:
        cmd_callback("LOCKDOWN")
        return {"success": True, "message": "Lockdown command sent."}
    raise HTTPException(status_code=500, detail="Command callback not configured.")

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
