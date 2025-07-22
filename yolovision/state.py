from datetime import datetime

shared_state = {
    "tracked": {},
    "history": {},
    "status": {},
    "counter": 0,
    "logs": [],
    "next_id": 0,
    "last_frame": None,
    "last_count_time": datetime.now(),
}

