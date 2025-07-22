
# Cotton Bale Detection System

A multi‑camera, real‑time cotton‑bale counting application with YOLO‑based detection, streaming servers, and a dashboard for monitoring and analytics.


## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [File Structure](#file-structure)
7. [How It Works](#how-it-works)
8. [License](#license)

---

## Features

* Two independent YOLO‑based detection pipelines for horizontal and vertical counting.
* FastAPI servers streaming raw and annotated video feeds.
* Flask dashboard for RTSP configuration, live viewing, and real‑time stats.
* REST API for analytics (live status, history, anomaly summary) backed by CSV logs.
* Automatic port cleanup and subprocess orchestration.

---

## Requirements

* Python 3.x
* Dependencies listed in `requirements.txt`:
  * `fastapi`, `uvicorn`, `flask`, `ultralytics`, `opencv-python`, `pandas`, etc.

---

## Installation

1. Clone the repository:

   ```bash
   git clone <repo-url>
   cd <repo-directory>
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

All configurable settings are in `config.py`:

* `MODEL_PATH_CAM1`, `MODEL_PATH_CAM2`: Paths to YOLO model weights.
* `STREAM_URL`, `STREAM_URL2`: HTTP endpoints for video feeds (ports 9000 & 7000).
* `FLASK_PORT`, `GRADIO_PORT`: Ports for the Flask UI and analytics API.
* `THRESHOLD`, `LINE_IN_Y`, `LINE_OUT_Y`: Detection confidence and line positions.

The RTSP URLs and user credentials are persisted in `user_info.json` via the UI.

---

## Usage

1. Run the entry point:

   ```bash
   python main.py
   ```

   This will:

   * Kill any existing processes on ports 7860, 7000, and 9000.
   * Launch the Flask dashboard (`app4.py`) on port 7860.

2. In your browser, navigate to `http://localhost:7860`:

   * Log in (default credentials: `0` / `0`).
   * Enter one or two RTSP stream URLs.
   * View raw and processed feeds in real time.
   * Monitor live status and stats via the dashboard.

3. Analytics API:

   * Run `app3.py` (Flask) on port 7864 or use the built‑in menu:

     ```bash
     python app3.py
     ```

   * Available endpoints:

     * `GET /api/camera/live`
     * `GET /api/camera/history?cameraId=<ID>&limit=<N>`
     * `GET /api/camera/anomalies?fromDate=<YYYY-MM-DD>&toDate=<YYYY-MM-DD>`

---

## File Structure

```
├── .gitignore
├── main.py               # Entry point to clean ports and launch dashboard
├── config.py             # Global settings and constants
├── logger.py             # Centralized logging setup
├── stream_handler.py     # FastAPI server + YOLO thread for camera 1 (port 9000)
├── stream_handler2.py    # FastAPI server + YOLO thread for camera 2 (port 7000)
├── app3.py               # Flask analytics API (port 7864)
├── app4.py               # Flask dashboard and orchestrator (port 7860)
├── detections_log.csv    # CSV log of all detection events
├── requirements.txt      # Python dependencies
├── user_info.json        # Persisted RTSP credentials
├── yolovision/           # YOLO pipeline for camera 1
│   ├── state.py
│   ├── utils.py
│   └── detection.py
└── yolovision2/          # YOLO pipeline for camera 2
    ├── state.py
    ├── utils.py
    └── detection.py


## How It Works

1. **Startup (`main.py`)**

   * Kills residual processes on key ports (7860, 7000, 9000).
   * Launches the Flask UI (`app4.py`).

2. **Dashboard & Orchestration (`app4.py`)**

   * User logs in and enters RTSP URLs.
   * Backend helpers spawn `stream_handler.py` and/or `stream_handler2.py` subprocesses and detection threads.
   * Provides pages to view raw and processed streams and polls live stats.

3. **Video Streaming + Detection**

   * `stream_handler.py` (port 9000):

     * FastAPI exposes `/video` (raw) and `/processed` (annotated from `shared_state`).
     * Detection thread (`yolovision/detection.py`) runs YOLO, counts bales crossing leftwards, updates `shared_state`, and logs to CSV.
   * `stream_handler2.py` (port 7000):

     * Parallel FastAPI service for camera 2, using `yolovision2` pipeline for bottom‑to‑top counting.

4. **Analytics API (`app3.py`)**

   * Reads `detections_log.csv` to serve JSON summaries:

     * Live status: active vs. offline (last 30s).
     * History: recent entries per camera.
     * Anomaly summary: counts per date range.

---

## License

MIT

```

---

Let me know if you'd like me to generate a README file from this or adapt it for a specific platform like GitHub!
```
