import re
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI()

class SolveRequest(BaseModel):
    query: str
    assets: Optional[List[str]] = []

def extract_numbers_from_query(query: str):
    """Extract numbers from 'Numbers: x,y,z' pattern strictly."""
    # Match "Numbers:" followed by comma/space separated digits
    list_match = re.search(r'[Nn]umbers?[:\s]+([\d,\s]+)', query)
    if list_match:
        raw = list_match.group(1)
        # Stop at first non-number/comma/space character (e.g. period, newline)
        raw = re.split(r'[^\d,\s]', raw)[0]
        nums = [int(n) for n in re.findall(r'\d+', raw)]
        return nums
    return []

@app.post("/solve")
async def solve_problem(request: SolveRequest):
    query = request.query
    q_low = query.lower()

    # ─── 1. NUMBER LIST OPERATIONS ───────────────────────────────────────────
    numbers = extract_numbers_from_query(query)

    if numbers:
        # Sum even numbers
        if re.search(r'sum\s+even', q_low):
            result = sum(n for n in numbers if n % 2 == 0)
            return {"output": str(result)}

        # Sum odd numbers
        if re.search(r'sum\s+odd', q_low):
            result = sum(n for n in numbers if n % 2 != 0)
            return {"output": str(result)}

        # Sum all
        if "sum" in q_low:
            return {"output": str(sum(numbers))}

        # Max
        if "max" in q_low or "maximum" in q_low or "largest" in q_low:
            return {"output": str(max(numbers))}

        # Min
        if "min" in q_low or "minimum" in q_low or "smallest" in q_low:
            return {"output": str(min(numbers))}

        # Count even
        if "count even" in q_low:
            return {"output": str(sum(1 for n in numbers if n % 2 == 0))}

        # Count odd
        if "count odd" in q_low:
            return {"output": str(sum(1 for n in numbers if n % 2 != 0))}

        # Average / mean
        if "average" in q_low or "mean" in q_low:
            avg = sum(numbers) / len(numbers)
            # Return int if whole number, else float
            return {"output": str(int(avg) if avg == int(avg) else round(avg, 2))}

        # Sort ascending
        if "sort" in q_low and ("asc" in q_low or "ascending" in q_low or "smallest" in q_low):
            return {"output": ", ".join(str(n) for n in sorted(numbers))}

        # Sort descending
        if "sort" in q_low and ("desc" in q_low or "descending" in q_low or "largest" in q_low):
            return {"output": ", ".join(str(n) for n in sorted(numbers, reverse=True))}

        # Default: return sum
        return {"output": str(sum(numbers))}

    # ─── 2. SINGLE NUMBER PARITY CHECK ───────────────────────────────────────
    # "Is X even?" / "Is X odd?"
    parity_match = re.search(r'is\s+(-?\d+)\s+(odd|even)', q_low)
    if parity_match:
        num = int(parity_match.group(1))
        parity = parity_match.group(2)
        if parity == "even":
            return {"output": "YES" if num % 2 == 0 else "NO"}
        else:
            return {"output": "YES" if num % 2 != 0 else "NO"}

    # ─── 3. DATE EXTRACTION ──────────────────────────────────────────────────
    date_pattern = r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
    date_match = re.search(date_pattern, query, re.IGNORECASE)
    if date_match:
        return {"output": date_match.group(0)}

    # ─── 4. ARITHMETIC EXPRESSIONS ───────────────────────────────────────────
    # "What is X + Y?" / "Calculate X * Y"
    arith_match = re.search(
        r'(?:what\s+is|calculate|compute|find)\s+(-?\d+)\s*([+\-*/×÷])\s*(-?\d+)',
        q_low
    )
    if arith_match:
        a, op, b = int(arith_match.group(1)), arith_match.group(2), int(arith_match.group(3))
        if op in ('+'):
            return {"output": str(a + b)}
        elif op in ('-'):
            return {"output": str(a - b)}
        elif op in ('*', '×'):
            return {"output": str(a * b)}
        elif op in ('/', '÷') and b != 0:
            result = a / b
            return {"output": str(int(result) if result == int(result) else round(result, 2))}

    # ─── 5. FALLBACK ─────────────────────────────────────────────────────────
    return {"output": "0"}
