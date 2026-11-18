from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import db

app = FastAPI()
db.init_db()
app.mount("/static", StaticFiles(directory="static"), name="static")


class WindowIn(BaseModel):
    user_id: str = Field(min_length=8, max_length=64)
    session_id: str = Field(min_length=8, max_length=64)
    label: Literal["sitting", "standing", "walking", "stairs_up", "stairs_down"]
    samples: list[list[float]] = Field(min_length=20, max_length=1000)
    user_agent: str = Field(default="", max_length=300)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/record")
def record_page():
    return FileResponse("static/record.html")


@app.get("/api/stats")
def get_stats():
    return db.stats()


@app.post("/api/windows")
def save_window(w: WindowIn):
    # Har bir namuna: [vaqt_ms, x, y, z]
    for s in w.samples:
        if len(s) != 4:
            raise HTTPException(400, "Har bir namuna 4 ta son bo'lishi kerak: vaqt, x, y, z.")
        if any(abs(v) > 200 for v in s[1:]):
            raise HTTPException(400, "Sensor qiymati ruxsat etilgan oraliqdan tashqarida.")

    duration_ms = w.samples[-1][0] - w.samples[0][0]
    if not (1000 <= duration_ms <= 5000):
        raise HTTPException(400, "Oyna uzunligi 1 dan 5 soniyagacha bo'lishi kerak.")

    sample_rate = (len(w.samples) - 1) / (duration_ms / 1000)
    if sample_rate < 5:
        raise HTTPException(400, "Sensor juda siyrak ma'lumot beryapti (5 Hz dan kam).")

    db.insert_window(w.user_id, w.session_id, w.label, w.samples, sample_rate, w.user_agent)
    return {"saved": True, "sample_rate": round(sample_rate, 1)}