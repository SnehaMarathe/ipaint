from __future__ import annotations
import json
import os
from typing import Any, Dict
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=api_key)

def summarize_chart(chart_payload: Dict[str, Any]) -> Dict[str, str]:
    client = _client()
    compact = {
        "core": chart_payload.get("core", {}),
        "planets": chart_payload.get("planets", {}),
        "vimshottari": chart_payload.get("vimshottari", {}),
    }
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        reasoning={"effort": "low"},
        text={"verbosity": "low"},
        input=[
            {
                "role": "developer",
                "content": (
                    "You are the astrologer for iPant Future. "
                    "The chart is already calculated. "
                    "Return JSON only with exact keys: personality, career, relationships, wealth. "
                    "Each value must be one concise paragraph of 18 to 35 words. "
                    "No bullets. No headings. No calculations."
                ),
            },
            {"role": "user", "content": json.dumps(compact, ensure_ascii=False)},
        ],
    )
    raw = response.output_text.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {
            "personality": "You carry a mix of steadiness and emotional drive, with strong instincts and a practical way of handling real life decisions.",
            "career": "Your best growth comes through disciplined effort, visible responsibility, and timely action rather than impulsive changes.",
            "relationships": "Warmth and directness matter in your bonds, but patience and listening strengthen emotional harmony.",
            "wealth": "Long-term planning and thoughtful risk-taking are more rewarding for you than rushed decisions.",
        }
    return {
        "personality": str(data.get("personality", "")),
        "career": str(data.get("career", "")),
        "relationships": str(data.get("relationships", "")),
        "wealth": str(data.get("wealth", "")),
    }

def answer_question(question: str, chart_payload: Dict[str, Any]) -> str:
    client = _client()
    compact = {
        "question": question,
        "core": chart_payload.get("core", {}),
        "planets": chart_payload.get("planets", {}),
        "vimshottari": chart_payload.get("vimshottari", {}),
        "summary": chart_payload.get("summary", {}),
    }
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        reasoning={"effort": "low"},
        text={"verbosity": "low"},
        input=[
            {
                "role": "developer",
                "content": (
                    "You are the astrologer for iPant Future. "
                    "Use only the provided chart context. "
                    "Answer the user's question in 70 to 120 words. "
                    "Be practical, premium, and direct. "
                    "No bullets. No headings. No technical calculation talk."
                ),
            },
            {"role": "user", "content": json.dumps(compact, ensure_ascii=False)},
        ],
    )
    return response.output_text.strip()
