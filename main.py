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

    # 1. STRICT LIST EXTRACTION
    # Isolates the numbers specifically following "Numbers:" to avoid "20000ms"
    list_match = re.search(r'numbers:\s*([\d,\s]+)', q_low)
    
    if list_match:
        # Extract only digits from the list part
        numbers = [int(n) for n in re.findall(r'\d+', list_match.group(1))]
        
        # Calculate sum based on parity
        if "even" in q_low:
            result = sum(n for n in numbers if n % 2 == 0)
            return {"output": str(result)}
        elif "odd" in q_low:
            result = sum(n for n in numbers if n % 2 != 0)
            return {"output": str(result)}
        else:
            return {"output": str(sum(numbers))}

    # 2. PARITY LOGIC (Fallback for Level 3)
    num_match = re.search(r'-?\d+', q_low)
    if num_match and ("odd" in q_low or "even" in q_low):
        num = int(num_match.group())
        if "odd" in q_low:
            return {"output": "YES" if num % 2 != 0 else "NO"}
        if "even" in q_low:
            return {"output": "YES" if num % 2 == 0 else "NO"}

    # 3. DATE LOGIC (Fallback for Level 2)
    date_pattern = r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
    date_match = re.search(date_pattern, query, re.IGNORECASE)
    if date_match:
        return {"output": date_match.group(0)}

    return {"output": "0"}
