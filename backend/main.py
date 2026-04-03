from __future__ import annotations
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ai_summary import summarize_chart, answer_question
from chart_engine import build_chart
from models import ChartRequest, AskRequest, AskResponse

load_dotenv()

app = FastAPI(title="iPant Future API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/chart")
def api_chart(payload: ChartRequest):
    try:
        chart = build_chart(
            name=payload.name,
            date_of_birth=payload.date_of_birth,
            time_of_birth=payload.time_of_birth,
            place_of_birth=payload.place_of_birth,
        )
        chart["summary"] = summarize_chart(chart)
        return chart
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/api/ask", response_model=AskResponse)
def api_ask(payload: AskRequest):
    try:
        return AskResponse(answer=answer_question(payload.question, payload.chart_context))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
