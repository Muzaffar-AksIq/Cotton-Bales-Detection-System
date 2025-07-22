import os
import sys
import json
import subprocess
import threading
import time
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from config import STREAM_URL,STREAM_URL2

# === Import your own modules here if needed ===
# from yolovision.streamer import start_flask_server
from yolovision.detection import start_yolo_detection
from yolovision2.detection import start_yolo_detection2
from yolovision.state import shared_state

# Mock for demo:
# shared_state = {"counter": 0, "logs": []}
PROCESSED_STREAM_URL = "http://localhost:9000/processed"  # Adjust as per your streamer
PROCESSED_STREAM_URL2 = "http://localhost:7000/processed"
app = Flask(__name__)
app.secret_key = "test1"

USER_INFO_FILE = "user_info.json"
VALID_USERNAME = "0"
VALID_PASSWORD = "0"

# Globals for backend process (as per your Gradio logic)
stream_process = None
flask_started = False

stream_process2 = None
flask_started2 = None

# --- Helper Functions ---
def load_saved_user_info():
    if os.path.exists(USER_INFO_FILE):
        try:
            with open(USER_INFO_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_user_info(name, password, link1,name2=None, password2=None, link2=None):
    data = {
        "name": name,
        "password": password,
        "link": link1,
        "name2": name2,
        "password2": password2,
        "link2": link2
    }
    with open(USER_INFO_FILE, "w") as f:
        json.dump(data, f)

def check_video_status():
    import cv2
    try:
        cap = cv2.VideoCapture(STREAM_URL2)
        if cap.isOpened():
            ret, _ = cap.read()
            cap.release()
            if ret:
                return True
    except Exception as e:
        print(f"Stream check failed: {e}")
    return False

def update_stats():
    # In your real app, this will use shared_state from yolovision.state
    print("yyooooooooo", shared_state["counter"])
    return str(shared_state["counter"]), "\n".join(shared_state["logs"][-10:])

def start_backend_if_needed(link):
    global stream_process, flask_started
    # Example backend subprocess logic, adjust as per your real setup
    if stream_process is None or stream_process.poll() is not None:
        # If using a detection backend Python script, start here
        stream_process = subprocess.Popen(
            [sys.executable, "stream_handler.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        # Log the process output
        def log_stream_output(process):
            for line in process.stdout:
                print("[stream_handler]", line.decode().strip())
            for line in process.stderr:
                print("[stream_handler][ERR]", line.decode().strip())
        threading.Thread(target=log_stream_output, args=(stream_process,), daemon=True).start()
        # time.sleep(2)
    if not flask_started:
        # threading.Thread(target=start_flask_server, daemon=True).start()
        threading.Thread(target=start_yolo_detection, daemon=True).start()
        print("Would start Flask streamer and YOLO detection here")
        flask_started = True

def start_backend_if_needed2(link):
    print("i'm in backend")
    global stream_process2, flask_started2
    # Example backend subprocess logic, adjust as per your real setup
    if stream_process2 is None or stream_process2.poll() is not None:
        # If using a detection backend Python script, start here
        print("starting stream handler 2")
        stream_process2 = subprocess.Popen(
            [sys.executable, "stream_handler2.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        # Log the process output
        def log_stream_output(process):
            for line in process.stdout:
                print("[stream_handler2]", line.decode().strip())
            for line in process.stderr:
                print("[stream_handler2][ERR]", line.decode().strip())
        threading.Thread(target=log_stream_output, args=(stream_process2,), daemon=True).start()
        # time.sleep(2)
    if not flask_started2:
        # threading.Thread(target=start_flask_server, daemon=True).start()
        threading.Thread(target=start_yolo_detection2, daemon=True).start()
        print("Would start Flask streamer and YOLO detection here")
        flask_started2 = True

# --- Flask Routes ---

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("rtsp_input"))
        else:
            return render_template("login.html", error="❌ Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route('/rtsp_input', methods=['GET', 'POST'])
def rtsp_input():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    saved = load_saved_user_info()
    if request.method == 'POST':
        name = "a"
        pwd = "a"
        link1 = request.form.get('rtsp1')
        name2 = "a"
        pwd2 = "a"
        link2 = request.form.get('rtsp2')
        if not link1:
            return render_template('rtsp_input.html', error="❗ Fill all fields", saved=saved)
        # Optionally start backend on submit
        if link2:
            print("yes")
            save_user_info(name, pwd, link1,name2, pwd2, link2)
            session['name'] = name
            session['password'] = pwd
            session['link'] = link1
            start_backend_if_needed(link1)
            start_backend_if_needed2(link2)
            return redirect(url_for("video_viewer2"))
            # start_backend_if_needed2(link2)
            # return redirect(url_for("video_viewer2"))
        save_user_info(name, pwd, link1)
        session['name'] = name
        session['password'] = pwd
        session['link'] = link1
        start_backend_if_needed(link1)
        return redirect(url_for("video_viewer"))
    return render_template('rtsp_input.html', error=None, saved=saved)

@app.route('/video_viewer')
def video_viewer():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    name = session.get('name')
    link = session.get('link')
    return render_template("video_viewer.html", name=name, link=link,
                           stream_url=STREAM_URL, processed_url=PROCESSED_STREAM_URL)

@app.route('/video_viewer2')
def video_viewer2():
    print("start html2")
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    name = session.get('name')
    link = session.get('link')
    name2 = session.get('name2')
    link2 = session.get('link2')
    return render_template("video_viewer2.html", name=name, link=link,
                           stream_url1=STREAM_URL, processed_url=PROCESSED_STREAM_URL,name2=name2, link2=link2,
                           stream_url2=STREAM_URL2, processed_url2=PROCESSED_STREAM_URL2)

@app.route('/check_status')
def check_status():
    status = check_video_status()
    return jsonify({
        "live": status
    })

@app.route('/get_stats')
def get_stats():
    count, logs = update_stats()
    return jsonify({
        "count": count,
        "logs": logs
    })

@app.route('/restart_app')
def restart_app():
    # (Optional) Add restart logic if running as a service
    os.execl(sys.executable, sys.executable, *sys.argv)
    return "Restarting..."

# --- Main ---
if __name__ == "__main__":
    app.run(debug=True, port=7860)
