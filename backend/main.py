from fastapi import FastAPI
from pydantic import BaseModel
import openai
from astrology import generate_chart

app=FastAPI()
openai.api_key="YOUR_OPENAI_API_KEY"

class UserInput(BaseModel):
    dob:str
    time:str
    place:str

class Question(BaseModel):
    question:str

@app.post("/generate")
def generate(data:UserInput):
    chart=generate_chart(data.dob,data.time,data.place)
    prompt=f"Birth chart: {chart}. Give reading."
    r=openai.ChatCompletion.create(model="gpt-4.1-mini",
    messages=[{"role":"user","content":prompt}])
    return {"reading":r.choices[0].message.content}

@app.post("/ask")
def ask(q:Question):
    r=openai.ChatCompletion.create(model="gpt-4.1-mini",
    messages=[{"role":"user","content":q.question}])
    return {"answer":r.choices[0].message.content}