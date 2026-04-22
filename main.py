import os
import re
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from groq import AsyncGroq
from dotenv import load_dotenv

# Load .env for local testing
load_dotenv()

app = FastAPI()

# Get the API key from environment variables
api_key = os.getenv("GROQ_API_KEY")

# Initialization: If this fails on Render, verify your Environment Variable in the dashboard!
client = AsyncGroq(api_key=api_key)

class SolveRequest(BaseModel):
    query: str
    assets: Optional[List[str]] = []

class SolveResponse(BaseModel):
    output: str

@app.get("/")
async def root():
    return {"status": "ok"}

@app.post("/solve", response_model=SolveResponse)
async def solve_problem(request: SolveRequest):
    query = request.query
    
    # --- LEVEL 2: DATE EXTRACTION RULE ---
    # This regex looks for patterns like "12 March 2024"
    date_pattern = r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
    date_match = re.search(date_pattern, query, re.IGNORECASE)
    
    if date_match:
        return SolveResponse(output=date_match.group(0))

    # --- LLM FALLBACK FOR ALL OTHER TASKS ---
    try:
        # We enforce "NO CHATTINESS" in the system prompt
        system_msg = "You are a data extraction agent. Output ONLY the answer. Do not use full sentences, do not add introductory phrases, do not provide conversational filler."
        
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": query}
            ],
            temperature=0.0,
            max_tokens=50
        )
        
        answer = response.choices[0].message.content.strip()
        return SolveResponse(output=answer)

    except Exception as e:
        return SolveResponse(output="Error processing request.")
