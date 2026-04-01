import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import OpenAI

from astrology import build_full_chart, chart_prompt_context

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "iPant Future !")
ALLOWED_ORIGINS = [item.strip() for item in os.getenv("ALLOWED_ORIGINS", "*").split(",") if item.strip()]
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")


@lru_cache
def get_openai_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BirthInput(BaseModel):
    name: str = Field(default="Friend", max_length=80)
    date_of_birth: str = Field(description="DD/MM/YYYY")
    time_of_birth: str = Field(description="HH:MM in 24-hour format")
    place_of_birth: str = Field(description="City, State, Country")


class AskInput(BaseModel):
    question: str = Field(min_length=3, max_length=1200)
    chart_context: dict


@app.get("/api/health")
def health():
    return {"ok": True, "app": APP_NAME}


@app.post("/api/chart")
def create_chart(payload: BirthInput):
    try:
        chart = build_full_chart(
            name=payload.name,
            dob=payload.date_of_birth,
            tob=payload.time_of_birth,
            place=payload.place_of_birth,
        )
        return chart
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/ask")
def ask_chart_question(payload: AskInput):
    client = get_openai_client()
    if client is None:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured on the backend.")

    system_prompt = (
        "You are the premium astrologer for iPant Future ! "
        "Answer using the provided Vedic chart context only. "
        "Be practical, warm, and clear. Avoid medical, legal, or financial certainty. "
        "Keep the answer under 250 words unless the user asks for more detail."
    )

    context = chart_prompt_context(payload.chart_context)
    user_input = f"Chart context:\n{context}\n\nUser question: {payload.question}"

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
    )

    return {"answer": response.output_text}
