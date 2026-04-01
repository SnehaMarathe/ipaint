from __future__ import annotations

import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_summary_prompt(chart: Dict[str, Any], question: str | None = None) -> str:
    compact = {
        "birth_details": chart["input"],
        "summary_facts": chart["summary_facts"],
        "planets": [
            {
                "name": p["name"],
                "sign": p["sign"],
                "house": p["house"],
                "degree_in_sign": p["degree_in_sign"],
                "retrograde": p["retrograde"],
            }
            for p in chart["planets"]
        ],
        "vimshottari": chart["vimshottari"],
    }
    if question:
        compact["question"] = question
    return json.dumps(compact, ensure_ascii=False, indent=2)


def get_summary(chart: Dict[str, Any], question: str | None = None) -> str:
    client = _client()
    payload = build_summary_prompt(chart, question)

    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        reasoning={"effort": "low"},
        text={"verbosity": "low"},
        input=[
            {
                "role": "developer",
                "content": (
                    "You are the astrologer for iPant Future. "
                    "The chart was already calculated by the backend. "
                    "Do not recalculate astronomy. "
                    "Return only a concise premium-quality interpretation. "
                    "Keep the output between 90 and 140 words. "
                    "No bullet points. No headings. No technical calculation talk. "
                    "Focus on the user's overall nature, current life theme, and one practical guidance point. "
                    "If a question is included, answer it briefly inside the same summary."
                ),
            },
            {
                "role": "user",
                "content": payload,
            },
        ],
    )
    return response.output_text.strip()
