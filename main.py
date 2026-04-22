import re
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class SolveRequest(BaseModel):
    query: str
    assets: Optional[List[str]] = []

@app.post("/solve")
async def solve_problem(request: SolveRequest):
    query = request.query
    q_low = query.lower()

    # 1. SUMMATION LOGIC (Strict)
    # We look specifically for a list pattern: numbers followed by parity requirement
    if any(k in q_low for k in ["sum", "add", "total", "calculate"]):
        # Extract the segment between "numbers:" and "." to avoid metadata like "20000ms"
        list_match = re.search(r'numbers:\s*([\d,\s]+)', q_low)
        if list_match:
            # Extract only the numbers found in the list segment
            numbers = [int(n) for n in re.findall(r'\d+', list_match.group(1))]
            
            if "even" in q_low:
                res = sum(n for n in numbers if n % 2 == 0)
                return {"output": str(res)}
            elif "odd" in q_low:
                res = sum(n for n in numbers if n % 2 != 0)
                return {"output": str(res)}
            else:
                return {"output": str(sum(numbers))}

    # 2. PARITY LOGIC (Level 3 - Is X odd/even?)
    # Only runs if sum keywords are NOT present
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

    # Default
    return {"output": "0"}
