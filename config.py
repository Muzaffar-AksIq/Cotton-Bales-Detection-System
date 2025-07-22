# App configuration (paths, constants, etc.)
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH_CAM1 = r"model\Cam1Model.pt"
MODEL_PATH_CAM2 = r"model\Cam1Model.pt"
STREAM_URL = "http://localhost:9000/video"  # <--- this line must exist
STREAM_URL2 = "http://localhost:7000/video"  # <--- this line must exist
FLASK_PORT = 7861
GRADIO_PORT = 7860
LINE_IN_Y = 100
LINE_OUT_Y = 300
THRESHOLD = 0.5
