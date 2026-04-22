import re
import os
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from groq import AsyncGroq

# Setup logging so you can see what is happening in the Render Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

class SolveRequest(BaseModel):
    query: str
    assets: Optional[List[str]] = []

class SolveResponse(BaseModel):
    output: str

@app.post("/solve", response_model=SolveResponse)
async def solve_problem(request: SolveRequest):
    query = request.query
    q_low = query.lower()
    logger.info(f"Received query: {query}") # Check this in Render Logs
    
    # 1. PARITY RULE (Updated to be more flexible)
    # This catches "Is 9 an odd number?", "Is 9 odd?", "Is 8 an even number?"
    num_match = re.search(r'(\d+)', q_low)
    if num_match and ("odd" in q_low or "even" in q_low):
        num = int(num_match.group(1))
        is_odd = (num % 2 != 0)
        
        if "odd" in q_low:
            return {"output": "YES" if is_odd else "NO"}
        if "even" in q_low:
            return {"output": "YES" if not is_odd else "NO"}

    # 2. DATE EXTRACTION RULE
    date_match = re.search(r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}', query, re.IGNORECASE)
    if date_match:
        return {"output": date_match.group(0)}

    # 3. STRICT LLM FALLBACK
    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a machine. Return ONLY the answer. If the question asks a Yes/No question, return YES or NO. Do not use periods, spaces, or sentences."},
                {"role": "user", "content": query}
            ],
            temperature=0,
            max_tokens=5
        )
        # Strip all potential junk
        answer = response.choices[0].message.content.strip().strip('.').upper()
        return {"output": answer}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"output": "ERROR"}
