import cv2
import time
import numpy as np
from datetime import datetime
from ultralytics import YOLO
from .state import shared_state
from logger import logger
from config import *
from yolovision.utils import log_detection_to_csv

tracked_objects = {}

# Simple center line for counting
CENTER_LINE_X = None

def wait_for_stream(url, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            cap.release()
            return True
        time.sleep(1)
    return False


def log_event(object_id, event_type, anomaly_detected=False, anomaly_type=None):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_msg = f"{timestamp} - {event_type}"
    logger.info(log_msg)
    shared_state["logs"].append(log_msg)

    line_count = shared_state.get("counter", 0)
    obj = tracked_objects.get(object_id, {})
    pos_x = obj.get("current_x", "NA")
    pos_y = obj.get("current_y", "NA")  # Use this for vertical
    counted = obj.get("counted", False)
    camera_id = "101"
    camera_name = "Camera 1"

    log_detection_to_csv(
        timestamp, object_id, event_type, line_count,
        pos_x, pos_y, counted, camera_id, camera_name,
        anomaly_detected, anomaly_type
    )


def start_yolo_detection():
    global CENTER_LINE_X
    logger.info("Starting YOLO detection thread")
    model = YOLO(MODEL_PATH_CAM1)

    if not wait_for_stream(STREAM_URL):
        logger.error("Stream not available after waiting. Exiting YOLO thread.")
        return

    cap = cv2.VideoCapture(STREAM_URL)
    if not cap.isOpened():
        logger.error("Failed to open video stream")
        return

    first_frame = True
    cx_list = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        H, W, _ = frame.shape
        
        # Set center line on first frame
        if first_frame:
            CENTER_LINE_X = (W // 2)-250  # Middle of frame for test i more move
            first_frame = False

        results = model.track(frame, persist=True, verbose=False)

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id.cpu().numpy().astype(int)
            classes = results[0].boxes.cls.cpu().numpy()
            class_names = results[0].names

            for box, obj_id, cls_id in zip(boxes, ids, classes):
                name = class_names[int(cls_id)].lower()
                if name not in ["cottonbale", "coveredbale"]:
                    continue

                x1, y1, x2, y2 = box
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                # Initialize new objects
                if obj_id not in tracked_objects:
                    side = "RIGHT" if cx > CENTER_LINE_X else "LEFT"
                    tracked_objects[obj_id] = {
                        "first_x": cx,
                        "current_x": cx,
                        "current_y": cy,  # testing new
                        "prev_x": cx,  # testing new
                        "started_side": side,
                        "counted": False
                    }
                obj = tracked_objects[obj_id]
                prev_x = obj["current_x"]
                obj["current_x"] = cx
                
                if not obj["counted"]:
                    cx_list.append(cx)
                    print(cx_list)
                    if len(cx_list) == 5:
                        print(cx_list)
                        is_decreasing = all(x > y for x, y in zip(cx_list, cx_list[1:]))
                        print("HEllo",is_decreasing)
                        if is_decreasing:
                            print("yes deacreasing")
                            check_sum = cx_list[0] - cx_list[4]
                            if check_sum > 50:
                                print("all_set")
                                shared_state["counter"] += 1
                                obj["counted"] = True
                                log_event(obj_id, f"Bale Detected. Total: {shared_state['counter']}")
                        cx_list = [] 
                
                # Draw bounding box
                if name == "coveredbale":
                    color = (0, 0, 255) if not obj["counted"] else (255, 0, 255)  # Red if not counted, magenta if counted
                else:
                    color = (0, 255, 0) if not obj["counted"] else (0, 255, 255)  # Green/yellow
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                
                # Labels
                status = "COUNTED" if obj["counted"] else f"Started {obj['started_side']}"
                cv2.putText(frame, f"ID: {obj_id}", (int(x1), int(y1)-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                cv2.putText(frame, f"x={cx} {status}", (int(x1), int(y2)+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)


        cv2.rectangle(frame, (10, 10), (250, 80), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (250, 80), (255, 255, 255), 2)
        cv2.putText(frame, f"COUNT: {shared_state['counter']}", (20, 55),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3)

        shared_state["last_frame"] = frame
        time.sleep(0.01)
    
    cap.release()
    logger.info("YOLO detection thread ended")