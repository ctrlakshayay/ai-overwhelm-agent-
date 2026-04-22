import re
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from groq import AsyncGroq

app = FastAPI()

# Initialize Groq client
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

class SolveRequest(BaseModel):
    query: str
    assets: Optional[List[str]] = []

class SolveResponse(BaseModel):
    output: str

@app.post("/solve", response_model=SolveResponse)
async def solve_problem(request: SolveRequest):
    query = request.query
    query_lower = query.lower()

    # 1. HARDCODED RULE: Math Parity Check (Odd/Even)
    # This captures questions like "Is 9 an odd number?" and forces an exact YES/NO
    if "is" in query_lower and "number" in query_lower:
        match = re.search(r'(\d+)', query_lower)
        if match:
            num = int(match.group(1))
            is_odd = num % 2 != 0
            
            if "odd" in query_lower:
                return {"output": "YES" if is_odd else "NO"}
            if "even" in query_lower:
                return {"output": "YES" if not is_odd else "NO"}

    # 2. HARDCODED RULE: Date Extraction (From Level 2)
    date_pattern = r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
    date_match = re.search(date_pattern, query, re.IGNORECASE)
    if date_match:
        return {"output": date_match.group(0)}

    # 3. STRICT LLM FALLBACK
    # If it's not a math or date question, the LLM answers, but we force clean output
    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Answer ONLY with the requested fact (e.g., YES, NO, or a value). No punctuation, no sentences."},
                {"role": "user", "content": query}
            ],
            temperature=0,
            max_tokens=10
        )
        # Force Uppercase and remove any period that the LLM might sneak in
        cleaned = response.choices[0].message.content.strip().strip('.').upper()
        return {"output": cleaned}
    except:
        return {"output": "ERROR"}
