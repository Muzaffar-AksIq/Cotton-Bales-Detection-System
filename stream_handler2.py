import json
import cv2
import threading
import asyncio
import numpy as np

from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Union

import uvicorn

from yolovision2.state import shared_state2
from yolovision2.detection import start_yolo_detection2

# — Load the RTSP link & user info —
with open("user_info.json", "r") as f:
    cfg = json.load(f)
STREAM_LINK = cfg["link2"]

# — Instantiate camera once for both endpoints —
class Camera:
    def __init__(self, url: Optional[Union[str, int]] = 0):
        self.cap = cv2.VideoCapture(url)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.lock = threading.Lock()

    def get_frame(self) -> bytes:
        with self.lock:
            ret, frame = self.cap.read()
            if not ret:
                return b''
            ret, jpeg = cv2.imencode('.jpg', frame)
            return jpeg.tobytes() if ret else b''

    def release(self):
        with self.lock:
            if self.cap.isOpened():
                self.cap.release()

camera = Camera(STREAM_LINK)

# — Start YOLO on startup, release camera on shutdown —
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Kick off your detection loop in a daemon thread
    threading.Thread(target=start_yolo_detection2, daemon=True).start()
    yield
    camera.release()

app = FastAPI(lifespan=lifespan)

# — Raw video feed —
async def gen_raw() -> AsyncGenerator[bytes, None]:
    while True:
        frame = camera.get_frame()
        if not frame:
            await asyncio.sleep(0.1)
            continue
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            frame +
            b"\r\n"
        )
        await asyncio.sleep(0)

@app.get("/video")
async def video_feed() -> StreamingResponse:
    return StreamingResponse(
        gen_raw(), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# — Processed (YOLO‐annotated) feed —
@app.get("/processed")
async def processed_feed() -> StreamingResponse:
    def gen_proc():
        while True:
            frame = shared_state2.get("last_frame")
            if frame is None:
                # blank fallback until detection writes something
                blank = 255 * np.ones((480,640,3), np.uint8)
                _, jpg = cv2.imencode('.jpg', blank)
            else:
                _, jpg = cv2.imencode('.jpg', frame)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                jpg.tobytes() +
                b"\r\n"
            )
    return StreamingResponse(
        gen_proc(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    print("I'm here2")
    uvicorn.run(app, host="0.0.0.0", port=7000)