from pydantic import BaseModel, Field


class BirthInput(BaseModel):
    date_of_birth: str = Field(..., examples=["1980-05-13"])
    time_of_birth: str = Field(..., examples=["20:15"])
    birth_place: str = Field(..., examples=["Pune, India"])


class ReadingRequest(BirthInput):
    question: str | None = None
