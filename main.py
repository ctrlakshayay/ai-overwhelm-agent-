import re
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from groq import AsyncGroq

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

    # 1. PARITY LOGIC (For "Is X odd/even?")
    # This regex is specifically tuned for parity questions.
    num_match = re.search(r'(\d+)', q_low)
    if num_match and ("odd" in q_low or "even" in q_low):
        num = int(num_match.group(1))
        # Odd logic
        if "odd" in q_low:
            return {"output": "YES" if num % 2 != 0 else "NO"}
        # Even logic
        if "even" in q_low:
            return {"output": "YES" if num % 2 == 0 else "NO"}

    # 2. DATE LOGIC (From Level 2)
    date_pattern = r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
    date_match = re.search(date_pattern, query, re.IGNORECASE)
    if date_match:
        return {"output": date_match.group(0)}

    # 3. STRICT LLM FALLBACK (Only for non-math/date queries)
    # This prevents the LLM from adding periods or "The answer is..."
    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a logic engine. If the question is Yes/No, reply ONLY with YES or NO. No punctuation. No sentences."},
                {"role": "user", "content": query}
            ],
            temperature=0,
            max_tokens=5
        )
        answer = response.choices[0].message.content.strip().strip('.').upper()
        return {"output": answer}
    except:
        return {"output": "NO"} # Default fallback
