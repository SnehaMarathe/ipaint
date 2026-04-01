from __future__ import annotations

import base64
import io
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import qrcode
import swisseph as swe
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="iPant Future API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

SESSIONS: dict[str, dict[str, Any]] = {}


class ChartRequest(BaseModel):
    name: str | None = None
    date_of_birth: str = Field(..., description="DD/MM/YYYY")
    birth_time: str = Field(..., description="HH:MM, 24h or 12h with AM/PM")
    place: str
    latitude: float
    longitude: float
    timezone: str = "Asia/Kolkata"


class AskRequest(BaseModel):
    session_id: str
    question: str


class PaymentConfirmRequest(BaseModel):
    session_id: str
    reference: str | None = None


@dataclass
class PlanetPosition:
    name: str
    longitude: float
    sign: str
    degree_in_sign: float
    nakshatra: str
    house: int
    retrograde: bool


def parse_birth_datetime(date_of_birth: str, birth_time: str, timezone_name: str) -> tuple[datetime, datetime]:
    date_formats = ["%d/%m/%Y", "%Y-%m-%d"]
    time_formats = ["%H:%M", "%I:%M%p", "%I:%M %p"]

    parsed_date = None
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_of_birth.strip(), fmt)
            break
        except ValueError:
            continue
    if not parsed_date:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD/MM/YYYY.")

    parsed_time = None
    cleaned = birth_time.strip().upper().replace(" ", "")
    for fmt in time_formats:
        try:
            parsed_time = datetime.strptime(cleaned, fmt)
            break
        except ValueError:
            continue
    if not parsed_time:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM or 08:15 PM.")

    try:
        tz = ZoneInfo(timezone_name)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unknown timezone: {timezone_name}") from exc

    local_dt = datetime(
        parsed_date.year,
        parsed_date.month,
        parsed_date.day,
        parsed_time.hour,
        parsed_time.minute,
        tzinfo=tz,
    )
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    return local_dt, utc_dt


def sign_from_longitude(longitude: float) -> tuple[str, float, int]:
    sign_index = int(longitude // 30) % 12
    return SIGNS[sign_index], longitude % 30, sign_index + 1


def nakshatra_from_longitude(longitude: float) -> str:
    index = int(longitude / (360 / 27)) % 27
    return NAKSHATRAS[index]


def compute_chart(payload: ChartRequest) -> dict[str, Any]:
    local_dt, utc_dt = parse_birth_datetime(payload.date_of_birth, payload.birth_time, payload.timezone)
    hour = utc_dt.hour + (utc_dt.minute / 60) + (utc_dt.second / 3600)
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour)
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    ecl_nut = swe.calc_ut(jd, swe.ECL_NUT)[0]
    eps_true = ecl_nut[0]
    houses, ascmc = swe.houses_ex(jd, payload.latitude, payload.longitude, b'P', swe.FLG_SIDEREAL)

    asc_long = ascmc[0]
    mc_long = ascmc[1]
    asc_sign, asc_deg, _ = sign_from_longitude(asc_long)
    mc_sign, mc_deg, _ = sign_from_longitude(mc_long)

    planets: list[dict[str, Any]] = []
    house_map: dict[int, list[str]] = {i: [] for i in range(1, 13)}

    for planet_name, planet_id in PLANETS.items():
        values, _ = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
        longitude = values[0] % 360
        latitude = values[1]
        speed = values[3]
        sign, degree_in_sign, _ = sign_from_longitude(longitude)
        house_pos = swe.house_pos(ascmc[2], payload.latitude, eps_true, (longitude, latitude), b'P')
        house = int(house_pos)
        if house < 1:
            house = 1
        if house > 12:
            house = 12

        planet = PlanetPosition(
            name=planet_name,
            longitude=round(longitude, 6),
            sign=sign,
            degree_in_sign=round(degree_in_sign, 2),
            nakshatra=nakshatra_from_longitude(longitude),
            house=house,
            retrograde=speed < 0,
        )
        planets.append(planet.__dict__)
        house_map[house].append(f"{planet.name} ({planet.sign} {planet.degree_in_sign}°)")

    ketu_long = (next(p["longitude"] for p in planets if p["name"] == "Rahu") + 180) % 360
    ketu_sign, ketu_deg, _ = sign_from_longitude(ketu_long)
    ketu_house_pos = swe.house_pos(ascmc[2], payload.latitude, eps_true, (ketu_long, 0.0), b'P')
    ketu_house = min(12, max(1, int(ketu_house_pos)))
    ketu = {
        "name": "Ketu",
        "longitude": round(ketu_long, 6),
        "sign": ketu_sign,
        "degree_in_sign": round(ketu_deg, 2),
        "nakshatra": nakshatra_from_longitude(ketu_long),
        "house": ketu_house,
        "retrograde": True,
    }
    planets.append(ketu)
    house_map[ketu_house].append(f"Ketu ({ketu_sign} {ketu_deg:.2f}°)")

    moon = next(p for p in planets if p["name"] == "Moon")
    sun = next(p for p in planets if p["name"] == "Sun")

    chart_data = {
        "system": "Vedic / Sidereal (Lahiri)",
        "ayanamsa": "Lahiri",
        "birth_details": {
            "name": payload.name or "Guest",
            "date_of_birth": payload.date_of_birth,
            "birth_time": payload.birth_time,
            "place": payload.place,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "timezone": payload.timezone,
            "local_iso": local_dt.isoformat(),
            "utc_iso": utc_dt.isoformat(),
        },
        "ascendant": {
            "sign": asc_sign,
            "degree": round(asc_deg, 2),
            "longitude": round(asc_long, 6),
        },
        "midheaven": {
            "sign": mc_sign,
            "degree": round(mc_deg, 2),
            "longitude": round(mc_long, 6),
        },
        "moon_sign": moon["sign"],
        "sun_sign": sun["sign"],
        "nakshatra": moon["nakshatra"],
        "planets": planets,
        "houses": [round(v, 6) for v in houses[:12]],
        "house_map": house_map,
    }
    return chart_data


def fallback_reading(chart: dict[str, Any]) -> str:
    moon_sign = chart["moon_sign"]
    asc_sign = chart["ascendant"]["sign"]
    sun_sign = chart["sun_sign"]
    nakshatra = chart["nakshatra"]
    return (
        f"Welcome to iPant Future! Your chart is calculated using the Vedic sidereal system. "
        f"Your Moon sign is {moon_sign}, your Ascendant is {asc_sign}, and your Sun sign is {sun_sign}. "
        f"Your Moon is placed in {nakshatra} nakshatra. This combination suggests a personality that blends instinct, "
        f"identity, and outer approach in a distinctive way. Review the chart below and ask your first free question."
    )


def get_openai_client() -> OpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def ai_chart_reading(chart: dict[str, Any]) -> str:
    client = get_openai_client()
    if client is None:
        return fallback_reading(chart)

    prompt = (
        "You are the astrology assistant for iPant Future. "
        "Use Vedic/sidereal astrology only. Give a concise premium reading in 5 short sections: "
        "Birth Chart Snapshot, Personality, Career Themes, Relationships, and First Free Question invite. "
        "Do not mention payment. Be warm and grounded.\n\n"
        f"Chart JSON:\n{json.dumps(chart, ensure_ascii=False)}"
    )
    try:
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=prompt,
        )
        return response.output_text.strip()
    except Exception:
        return fallback_reading(chart)


def ai_answer(chart: dict[str, Any], question: str) -> str:
    client = get_openai_client()
    if client is None:
        moon = chart["moon_sign"]
        asc = chart["ascendant"]["sign"]
        return (
            f"Based on your Vedic chart with Moon in {moon} and Ascendant in {asc}, here is a grounded answer: "
            f"{question} should be interpreted through your chart’s balance of initiative, discipline, and timing. "
            "For production, connect an OpenAI API key to generate richer personalized answers."
        )

    prompt = (
        "You are the astrology assistant for iPant Future. Use only the chart data provided. "
        "Answer exactly one user question in a clear, personalized way using Vedic astrology. "
        "Do not answer more than asked. Avoid certainty claims. End with one practical takeaway.\n\n"
        f"Chart JSON:\n{json.dumps(chart, ensure_ascii=False)}\n\n"
        f"User question: {question}"
    )
    try:
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=prompt,
        )
        return response.output_text.strip()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI answer failed: {exc}") from exc


@app.get("/api/config")
def get_config() -> dict[str, Any]:
    return {
        "headline": "iPant Future !",
        "upi_id": os.getenv("UPI_ID", "demo@upi"),
        "payee_name": os.getenv("PAYEE_NAME", "iPant Future"),
        "currency": "INR",
        "price_per_question": 1,
        "payment_note": "Demo mode: replace /api/payment/confirm with a real payment webhook in production.",
    }


@app.get("/api/payment/qr")
def get_qr(amount: int = 1, session_id: str | None = None) -> dict[str, Any]:
    upi_id = os.getenv("UPI_ID", "demo@upi")
    payee_name = os.getenv("PAYEE_NAME", "iPant Future")
    transaction_ref = session_id or str(uuid.uuid4())
    upi_url = f"upi://pay?pa={upi_id}&pn={payee_name}&am={amount}&cu=INR&tn=iPant%20Future%20Question%20Unlock&tr={transaction_ref}"
    image = qrcode.make(upi_url)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return {"upi_url": upi_url, "qr_data_uri": f"data:image/png;base64,{encoded}"}


@app.post("/api/chart")
def create_chart(payload: ChartRequest) -> dict[str, Any]:
    chart = compute_chart(payload)
    session_id = str(uuid.uuid4())
    reading = ai_chart_reading(chart)
    SESSIONS[session_id] = {
        "chart": chart,
        "free_question_used": False,
        "paid_questions": 0,
        "history": [],
    }
    return {
        "session_id": session_id,
        "headline": "iPant Future !",
        "chart": chart,
        "reading": reading,
        "free_question_used": False,
        "paid_questions": 0,
    }


@app.post("/api/ask")
def ask_question(payload: AskRequest) -> dict[str, Any]:
    session = SESSIONS.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Generate the chart again.")

    if not session["free_question_used"]:
        answer = ai_answer(session["chart"], payload.question)
        session["free_question_used"] = True
        session["history"].append({"question": payload.question, "answer": answer, "paid": False})
        return {
            "answer": answer,
            "free_question_used": True,
            "paid_questions": session["paid_questions"],
            "requires_payment_next": True,
        }

    if session["paid_questions"] <= 0:
        raise HTTPException(
            status_code=402,
            detail="Your free question has been used. Please pay ₹1 via the QR code to unlock the next question.",
        )

    answer = ai_answer(session["chart"], payload.question)
    session["paid_questions"] -= 1
    session["history"].append({"question": payload.question, "answer": answer, "paid": True})
    return {
        "answer": answer,
        "free_question_used": True,
        "paid_questions": session["paid_questions"],
        "requires_payment_next": True,
    }


@app.post("/api/payment/confirm")
def confirm_payment(payload: PaymentConfirmRequest) -> dict[str, Any]:
    session = SESSIONS.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    session["paid_questions"] += 1
    return {
        "ok": True,
        "message": "Demo payment confirmed. One paid question unlocked.",
        "paid_questions": session["paid_questions"],
    }


@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")
