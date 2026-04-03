from typing import Any, Dict
from pydantic import BaseModel, Field

class ChartRequest(BaseModel):
    name: str = Field(default="Guest")
    date_of_birth: str = Field(..., description="DD/MM/YYYY")
    time_of_birth: str = Field(..., description="HH:MM in 24-hour format")
    place_of_birth: str = Field(..., description="City, State, Country")

class AskRequest(BaseModel):
    question: str
    chart_context: Dict[str, Any]

class AskResponse(BaseModel):
    answer: str
