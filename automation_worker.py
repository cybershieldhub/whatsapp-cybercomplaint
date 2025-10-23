# automation_worker.py
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import random
import string

app = FastAPI(title="Mock Automation Worker")

class PrefillRequest(BaseModel):
    session_id: str
    complaint_data: dict = {}
    evidence_urls: list = []

class CompleteRequest(BaseModel):
    token: str
    captcha_text: str
    otp: str | None = None

def _random_token():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=20))

@app.post("/prefill")
def prefill(req: PrefillRequest):
    # return captcha url and token
    token = _random_token()
    captcha_url = f"https://mock-captcha.example.com/{req.session_id}?t={token}"
    return {"captcha_url": captcha_url, "token": token}

@app.post("/complete")
def complete(req: CompleteRequest):
    # very simple validation: accept if captcha_text length >= 3
    if not req.captcha_text or len(req.captcha_text.strip()) < 3:
        return {"status": "error", "error": "invalid captcha"}
    # simulate success
    complaint_id = f"complaint_{req.token[:8]}"
    return {"status": "submitted", "complaint_id": complaint_id}

if __name__ == "__main__":
    uvicorn.run("automation_worker:app", host="127.0.0.1", port=5001, reload=False)
