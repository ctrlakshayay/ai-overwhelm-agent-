import re
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class SolveRequest(BaseModel):
    query: str
    assets: Optional[List[str]] = []

# ── HEALTH ────────────────────────────────────────────────────────────────────
@app.get("/")
async def health():
    return {"status": "ok"}

@app.get("/health")
async def health2():
    return {"status": "ok"}

# ── HELPERS ───────────────────────────────────────────────────────────────────

def extract_name_value_pairs(query: str):
    """
    Extracts (name, value) pairs from patterns like:
    - 'Alice scored 80, Bob scored 90'
    - 'Alice: 80, Bob: 90'
    - 'Alice has 80 points, Bob has 90 points'
    - 'Alice=80, Bob=90'
    """
    # Pattern 1: "Name scored/got/has/earned NUMBER"
    pairs = re.findall(
        r'([A-Z][a-z]+)\s+(?:scored|got|has|earned|received|made|achieved|with)\s+(\d+(?:\.\d+)?)',
        query
    )
    if pairs:
        return [(name, float(val)) for name, val in pairs]

    # Pattern 2: "Name: NUMBER" or "Name = NUMBER"
    pairs = re.findall(r'([A-Z][a-z]+)\s*[=:]\s*(\d+(?:\.\d+)?)', query)
    if pairs:
        return [(name, float(val)) for name, val in pairs]

    # Pattern 3: "Name (NUMBER)" or "Name - NUMBER"
    pairs = re.findall(r'([A-Z][a-z]+)\s*[\(\-]\s*(\d+(?:\.\d+)?)', query)
    if pairs:
        return [(name, float(val)) for name, val in pairs]

    return []

def extract_numbers(query: str):
    match = re.search(r'[Nn]umbers?[:\s]+([\d,\s]+)', query)
    if match:
        raw = match.group(1)
        raw = re.split(r'[^\d,\s]', raw)[0]
        return [int(n) for n in re.findall(r'\d+', raw)]
    return []

# ── MAIN SOLVE ────────────────────────────────────────────────────────────────
@app.post("/solve")
async def solve(request: SolveRequest):
    query = request.query
    q = query.lower()

    # ── LEVEL 5: NAME-VALUE COMPARISONS ──────────────────────────────────────
    pairs = extract_name_value_pairs(query)

    if pairs:
        # "Who scored highest / most / best / maximum?"
        if any(w in q for w in ["highest", "most", "best", "maximum", "max", "greater", "more", "top", "winner", "won", "largest", "bigger", "better"]):
            winner = max(pairs, key=lambda x: x[1])
            return {"output": winner[0]}

        # "Who scored lowest / least / minimum / worst / fewest?"
        if any(w in q for w in ["lowest", "least", "minimum", "min", "worst", "fewest", "smaller", "smaller", "bottom", "lost"]):
            loser = min(pairs, key=lambda x: x[1])
            return {"output": loser[0]}

        # "What is the highest/max score?"
        if any(w in q for w in ["highest score", "max score", "maximum score", "best score", "top score"]):
            return {"output": str(int(max(v for _, v in pairs)) if max(v for _, v in pairs) == int(max(v for _, v in pairs)) else max(v for _, v in pairs))}

        # "What is the lowest/min score?"
        if any(w in q for w in ["lowest score", "min score", "minimum score", "worst score"]):
            return {"output": str(int(min(v for _, v in pairs)) if min(v for _, v in pairs) == int(min(v for _, v in pairs)) else min(v for _, v in pairs))}

        # "What is the difference?"
        if "difference" in q or "how much more" in q or "how much less" in q:
            vals = [v for _, v in pairs]
            diff = abs(vals[0] - vals[1]) if len(vals) >= 2 else 0
            return {"output": str(int(diff) if diff == int(diff) else diff)}

        # "What is the total / sum?"
        if "total" in q or "sum" in q or "combined" in q or "together" in q:
            total = sum(v for _, v in pairs)
            return {"output": str(int(total) if total == int(total) else total)}

        # "What is the average?"
        if "average" in q or "mean" in q:
            avg = sum(v for _, v in pairs) / len(pairs)
            return {"output": str(int(avg) if avg == int(avg) else round(avg, 2))}

        # "How many scored above X?"
        above = re.search(r'(?:scored|score)\s+above\s+(\d+)', q)
        if above:
            threshold = float(above.group(1))
            count = sum(1 for _, v in pairs if v > threshold)
            return {"output": str(count)}

        # "How many scored below X?"
        below = re.search(r'(?:scored|score)\s+below\s+(\d+)', q)
        if below:
            threshold = float(below.group(1))
            count = sum(1 for _, v in pairs if v < threshold)
            return {"output": str(count)}

        # Default for pairs: return name with highest value
        winner = max(pairs, key=lambda x: x[1])
        return {"output": winner[0]}

    # ── LEVEL 4: NUMBER LIST OPERATIONS ──────────────────────────────────────
    numbers = extract_numbers(query)

    if numbers:
        if re.search(r'sum\s+even', q):
            return {"output": str(sum(n for n in numbers if n % 2 == 0))}
        if re.search(r'sum\s+odd', q):
            return {"output": str(sum(n for n in numbers if n % 2 != 0))}
        if "sum" in q:
            return {"output": str(sum(numbers))}
        if "max" in q or "maximum" in q or "largest" in q:
            return {"output": str(max(numbers))}
        if "min" in q or "minimum" in q or "smallest" in q:
            return {"output": str(min(numbers))}
        if "count even" in q:
            return {"output": str(sum(1 for n in numbers if n % 2 == 0))}
        if "count odd" in q:
            return {"output": str(sum(1 for n in numbers if n % 2 != 0))}
        if "average" in q or "mean" in q:
            avg = sum(numbers) / len(numbers)
            return {"output": str(int(avg) if avg == int(avg) else round(avg, 2))}
        if "sort" in q and ("desc" in q or "descending" in q):
            return {"output": ", ".join(str(n) for n in sorted(numbers, reverse=True))}
        if "sort" in q:
            return {"output": ", ".join(str(n) for n in sorted(numbers))}
        return {"output": str(sum(numbers))}

    # ── LEVEL 3: PARITY CHECK ─────────────────────────────────────────────────
    parity = re.search(r'is\s+(-?\d+)\s+(odd|even)', q)
    if parity:
        num = int(parity.group(1))
        kind = parity.group(2)
        if kind == "even":
            return {"output": "YES" if num % 2 == 0 else "NO"}
        else:
            return {"output": "YES" if num % 2 != 0 else "NO"}

    # ── LEVEL 2: DATE EXTRACTION ──────────────────────────────────────────────
    date = re.search(
        r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August'
        r'|September|October|November|December)\s+\d{4}',
        query, re.IGNORECASE
    )
    if date:
        return {"output": date.group(0)}

    # ── ARITHMETIC ────────────────────────────────────────────────────────────
    arith = re.search(r'(-?\d+)\s*([+\-*/])\s*(-?\d+)', query)
    if arith:
        a, op, b = int(arith.group(1)), arith.group(2), int(arith.group(3))
        if op == '+':
            return {"output": str(a + b)}
        elif op == '-':
            return {"output": str(a - b)}
        elif op == '*':
            return {"output": str(a * b)}
        elif op == '/' and b != 0:
            r = a / b
            return {"output": str(int(r) if r == int(r) else round(r, 2))}

    return {"output": "0"}

# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
