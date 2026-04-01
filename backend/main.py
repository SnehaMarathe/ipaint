from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_summary import get_summary
from chart_engine import build_chart
from models import BirthInput, ReadingRequest

load_dotenv()

app = FastAPI(title="iPant Future Astrology Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/chart")
def chart_endpoint(payload: BirthInput) -> dict:
    chart = build_chart(
        date_of_birth=payload.date_of_birth,
        time_of_birth=payload.time_of_birth,
        birth_place=payload.birth_place,
    )
    return {"chart": chart}


@app.post("/api/reading")
def reading_endpoint(payload: ReadingRequest) -> dict:
    chart = build_chart(
        date_of_birth=payload.date_of_birth,
        time_of_birth=payload.time_of_birth,
        birth_place=payload.birth_place,
    )
    summary = get_summary(chart, payload.question)
    return {"chart": chart, "summary": summary}
