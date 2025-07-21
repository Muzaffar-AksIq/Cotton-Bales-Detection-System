# Stream handling logic
# import asyncio
# from fastapi import FastAPI, Response
# from fastapi.responses import StreamingResponse
# import cv2
# import threading
# from typing import AsyncGenerator
# from contextlib import asynccontextmanager
# import uvicorn
# from typing import Optional, Union
# import json
# import numpy as np
# from yolovision.state import shared_state

# with open("user_info.json", "r") as f:
#     data = json.load(f)

# stream_link = data["link"]
# username = data["name"]

# print(f"Received Stream Link: {stream_link}")



# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """
#     Lifespan context manager for startup and shutdown events.
#     """
#     try:
#         yield
#     except asyncio.exceptions.CancelledError as error:
#         print(error.args)
#     finally:
#         camera.release()
#         print("Camera resource released.")

# app = FastAPI(lifespan=lifespan)


# @app.get("/video")
# async def video_feed():
#     return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

# @app.get("/processed")
# async def processed():
#     def gen_proc():
#         while True:
#             frame = shared_state.get("last_frame")
#             if frame is not None:
#                 _, jpg = cv2.imencode(".jpg", frame)
#                 yield (
#                   b"--frame\r\n"
#                   b"Content-Type: image/jpeg\r\n\r\n" +
#                   jpg.tobytes() +
#                   b"\r\n"
#                 )
#             else:
#                 blank = 255 * np.ones((480,640,3), np.uint8)
#                 _, jpg = cv2.imencode(".jpg", blank)
#                 yield (b"--frame\r\n"
#                        b"Content-Type: image/jpeg\r\n\r\n" +
#                        jpg.tobytes() +
#                        b"\r\n")
#     return StreamingResponse(gen_proc(), media_type="multipart/x-mixed-replace; boundary=frame")


# class Camera:
#     """
#     A class to handle video capture from a camera.
#     """

#     def __init__(self, url: Optional[Union[str, int]] = 0) -> None:
#         """
#         Initialize the camera.

#         :param camera_index: Index of the camera to use.
#         """
#         self.cap = cv2.VideoCapture(url)
#         self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # fr testing 
#         self.lock = threading.Lock()

#     def get_frame(self) -> bytes:
#         """
#         Capture a frame from the camera.

#         :return: JPEG encoded image bytes.
#         """
#         with self.lock:
#             ret, frame = self.cap.read()
#             if not ret:
#                 return b''

#             ret, jpeg = cv2.imencode('.jpg', frame)
#             if not ret:
#                 return b''

#             return jpeg.tobytes()

#     def release(self) -> None:
#         """
#         Release the camera resource.
#         """
#         with self.lock:
#             if self.cap.isOpened():
#                 self.cap.release()


# async def gen_frames() -> AsyncGenerator[bytes, None]:
#     """
#     An asynchronous generator function that yields camera frames.

#     :yield: JPEG encoded image bytes.
#     """
#     try:
#         while True:
#             frame = camera.get_frame()
#             if frame:
#                 yield (b'--frame\r\n'
#                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#             else:
#                 break
#             await asyncio.sleep(0)
            
#     except (asyncio.CancelledError, GeneratorExit):
#         print("Frame generation cancelled.")
#     finally:
#         print("Frame generator exited.")


# @app.get("/video")
# async def video_feed() -> StreamingResponse:
#     """
#     Video streaming route.

#     :return: StreamingResponse with multipart JPEG frames.
#     """
#     return StreamingResponse(
#         gen_frames(),
#         media_type='multipart/x-mixed-replace; boundary=frame'
#     )


# @app.get("/snapshot")
# async def snapshot() -> Response:
#     """
#     Snapshot route to get a single frame.

#     :return: Response with JPEG image.
#     """
#     frame = camera.get_frame()
#     if frame:
#         return Response(content=frame, media_type="image/jpeg")
#     else:
#         return Response(status_code=404, content="Camera frame not available.")


# async def main():
#     """
#     Main entry point to run the Uvicorn server.
#     """
#     config = uvicorn.Config(app, host='0.0.0.0', port=9000)
#     server = uvicorn.Server(config)

#     # Run the server
#     await server.serve()

    

# if __name__ == '__main__':
#     # Usage example: Streaming default camera for local webcam:
#     print(stream_link,"aaaaaaaaaaaaaaaaaaaasssssssssssssssssssssssssss")
#     camera = Camera(stream_link)
#     print(stream_link,"aaaaaaaaaaaaaaaaaaaasssssssssssssssssssssssssss")
#     # camera = Camera('rtsp://localhost:8554/webcam.sdp')
#     # camera = Camera('rtsp://192.168.200.78:8554/mystream')
#     # Usage example: Streaming the camera for a specific camera index:
#     # camera = Camera(0)

#     # Usage example 3: Streaming an IP camera:
#     # camera = Camera('rtsp://user:password@ip_address:port/')

#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print("Server stopped by user.")


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

from yolovision.state import shared_state
from yolovision.detection import start_yolo_detection

# — Load the RTSP link & user info —
with open("user_info.json", "r") as f:
    cfg = json.load(f)
STREAM_LINK = cfg["link"]

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
    threading.Thread(target=start_yolo_detection, daemon=True).start()
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
            frame = shared_state.get("last_frame")
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
    uvicorn.run(app, host="0.0.0.0", port=9000)
