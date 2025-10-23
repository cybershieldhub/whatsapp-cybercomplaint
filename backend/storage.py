# backend/storage.py
import os
import requests
from urllib.parse import urlparse
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

STORAGE_MODE = os.getenv("STORAGE_MODE", "local")  # "local" or "s3"
LOCAL_UPLOAD_DIR = os.getenv("LOCAL_UPLOAD_DIR", "uploads")
os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)


def _safe_filename(name: str) -> str:
    # very simple sanitization
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".", "_")).strip()


def save_bytes_locally(filename: str, content: bytes) -> str:
    safe_name = _safe_filename(filename)
    path = Path(LOCAL_UPLOAD_DIR) / safe_name
    with open(path, "wb") as f:
        f.write(content)
    # Return a path served by FastAPI static mount (e.g. /uploads/filename)
    return f"/{LOCAL_UPLOAD_DIR}/{safe_name}"


def download_url_to_local(url: str, filename_hint: Optional[str] = None, headers: Optional[dict] = None) -> str:
    """
    Download from given URL and save locally. Returns public path (e.g. /uploads/xxx)
    headers: optional dict for auth/headers when downloading (Twilio media may need basic auth)
    """
    resp = requests.get(url, headers=headers or {}, timeout=30)
    resp.raise_for_status()

    if filename_hint:
        filename = filename_hint
    else:
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path) or f"file_{os.urandom(6).hex()}"

    return save_bytes_locally(filename, resp.content)


# -- S3 stub (you can implement later) --
def upload_bytes_to_s3(filename: str, content: bytes) -> str:
    """
    Placeholder for S3 upload. Implement with boto3 if you choose S3.
    Should return the public URL of the uploaded file.
    """
    raise NotImplementedError("S3 upload not implemented. Use local mode for now.")
