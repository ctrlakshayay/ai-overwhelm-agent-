import re
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class SolveRequest(BaseModel):
    query: str
    assets: Optional[List[str]] = []

class SolveResponse(BaseModel):
    output: str

@app.post("/solve", response_model=SolveResponse)
async def solve_problem(request: SolveRequest):
    query = request.query
    q_low = query.lower()

    # 1. UNIVERSAL MATH LOGIC (Level 4)
    # Detects: sum, add, total, calculate. Detects: -1, 0, 1, 100.
    # Logic: Finds integers, filters by parity, sums them.
    numbers = [int(n) for n in re.findall(r'-?\d+', query)]
    
    # Trigger if math keywords are present AND numbers exist
    math_keywords = ["sum", "add", "total", "calculate"]
    if numbers and any(word in q_low for word in math_keywords):
        if "even" in q_low:
            result = sum(n for n in numbers if n % 2 == 0)
            return {"output": str(result)}
        elif "odd" in q_low:
            result = sum(n for n in numbers if n % 2 != 0)
            return {"output": str(result)}

    # 2. PARITY LOGIC (Level 3 - "Is X odd/even?")
    num_match = re.search(r'-?\d+', q_low)
    if num_match and ("odd" in q_low or "even" in q_low):
        num = int(num_match.group())
        if "odd" in q_low:
            return {"output": "YES" if num % 2 != 0 else "NO"}
        if "even" in q_low:
            return {"output": "YES" if num % 2 == 0 else "NO"}

    # 3. DATE LOGIC (Level 2)
    date_pattern = r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
    date_match = re.search(date_pattern, query, re.IGNORECASE)
    if date_match:
        return {"output": date_match.group(0)}

    # 4. DEFAULT
    return {"output": "0"}
