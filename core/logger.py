from datetime import datetime

def _ts():
    return datetime.now().strftime("%H:%M:%S")

def info(message):
    print(f"[{_ts()}] INFO  {message}")

def success(message):
    print(f"[{_ts()}] PASS  {message}")

def warning(message):
    print(f"[{_ts()}] WARN  {message}")

def error(message):
    print(f"[{_ts()}] FAIL  {message}")
