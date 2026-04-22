import re
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class SolveRequest(BaseModel):
    query: str
    assets: Optional[List[str]] = []

# No response_model here to prevent FastAPI validation errors
@app.post("/solve")
async def solve_problem(request: SolveRequest):
    query = request.query
    q_low = query.lower()

    # 1. SUMMATION LOGIC (Highest priority)
    # This logic handles "Sum even/odd numbers"
    if any(k in q_low for k in ["sum", "add", "total", "calculate"]):
        # Extract numbers, handling commas or spaces
        numbers = [int(n) for n in re.findall(r'-?\d+', query)]
        if numbers:
            if "even" in q_low:
                res = sum(n for n in numbers if n % 2 == 0)
                return {"answer": str(res)}
            elif "odd" in q_low:
                res = sum(n for n in numbers if n % 2 != 0)
                return {"answer": str(res)}
            else:
                # Default sum if no parity specified
                return {"answer": str(sum(numbers))}

    # 2. PARITY LOGIC
    num_match = re.search(r'-?\d+', q_low)
    if num_match and ("odd" in q_low or "even" in q_low):
        num = int(num_match.group())
        if "odd" in q_low:
            return {"answer": "YES" if num % 2 != 0 else "NO"}
        if "even" in q_low:
            return {"answer": "YES" if num % 2 == 0 else "NO"}

    # 3. DATE LOGIC
    date_pattern = r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
    date_match = re.search(date_pattern, query, re.IGNORECASE)
    if date_match:
        return {"answer": date_match.group(0)}

    # Default fallback
    return {"answer": "0"}
