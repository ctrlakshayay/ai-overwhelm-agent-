import re
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
    
    # 1. STRICT REGEX DATE EXTRACTION
    # Matches patterns like "12 March 2024" or "25 December 2025"
    date_pattern = r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
    match = re.search(date_pattern, query, re.IGNORECASE)
    
    if match:
        # Returning ONLY the string found, no extra words, no periods
        return {"output": match.group(0)}

    # 2. FALLBACK: Simple identity for other tasks
    # If it's not a date, return the query or a placeholder
    return {"output": query}
