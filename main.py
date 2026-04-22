import re
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class SolveRequest(BaseModel):
    query: str
    assets: Optional[List[str]] = []

@app.get("/")
async def health():
    return {"status": "ok"}

# ── DEBUG: see exactly what your server extracts ──────────────────────────────
@app.get("/debug")
async def debug():
    query = "Alice scored 80, Bob scored 90. Who scored highest?"
    pairs = get_pairs(query)
    q = query.lower()
    highest_kw = ["highest","most","best","maximum","max","largest","top","winner","won","greater","more","bigger","better"]
    hit = [w for w in highest_kw if w in q]
    result = max(pairs, key=lambda x: x[1])[0] if pairs else "NO PAIRS FOUND"
    return {"pairs": pairs, "keywords_hit": hit, "output": result}

# ── PAIR EXTRACTOR ────────────────────────────────────────────────────────────
def get_pairs(query: str):
    # Pattern 1: "Name scored/got/has/earned/received/made/achieved NUMBER"
    pairs = re.findall(
        r'([A-Z][a-zA-Z]+)\s+(?:scored|got|has|earned|received|made|achieved|with|marks?)\s+(\d+(?:\.\d+)?)',
        query
    )
    if pairs:
        return [(n, float(v)) for n, v in pairs]

    # Pattern 2: "Name: NUMBER" or "Name = NUMBER"
    pairs = re.findall(r'([A-Z][a-zA-Z]+)\s*[=:]\s*(\d+(?:\.\d+)?)', query)
    if pairs:
        return [(n, float(v)) for n, v in pairs]

    # Pattern 3: "Name NUMBER points/marks/score"
    pairs = re.findall(
        r'([A-Z][a-zA-Z]+)\s+(\d+(?:\.\d+)?)\s*(?:points?|marks?|score)',
        query
    )
    if pairs:
        return [(n, float(v)) for n, v in pairs]

    return []

# ── MAIN ENDPOINT ─────────────────────────────────────────────────────────────
@app.post("/solve")
async def solve(request: SolveRequest):
    query = request.query
    q = query.lower()

    # ── LEVEL 5: NAME-VALUE PAIRS ─────────────────────────────────────────────
    pairs = get_pairs(query)

    if pairs:
        highest_kw = ["highest","most","best","maximum","max","largest","top","winner","won","greater","more","bigger","better","leads","ahead"]
        lowest_kw  = ["lowest","least","minimum","min","worst","fewest","smallest","bottom","less","fewer","lower","behind","last"]

        if any(w in q for w in highest_kw):
            return {"output": max(pairs, key=lambda x: x[1])[0]}

        if any(w in q for w in lowest_kw):
            return {"output": min(pairs, key=lambda x: x[1])[0]}

        if "difference" in q or "how much more" in q or "how much less" in q or "gap" in q:
            vals = sorted([v for _, v in pairs])
            diff = vals[-1] - vals[0]
            return {"output": str(int(diff) if diff == int(diff) else diff)}

        if "total" in q or "sum" in q or "combined" in q or "together" in q or "both" in q:
            total = sum(v for _, v in pairs)
            return {"output": str(int(total) if total == int(total) else total)}

        if "average" in q or "mean" in q:
            avg = sum(v for _, v in pairs) / len(pairs)
            return {"output": str(int(avg) if avg == int(avg) else round(avg, 2))}

        if "how many" in q and "above" in q:
            threshold = float(re.search(r'above\s+(\d+)', q).group(1))
            return {"output": str(sum(1 for _, v in pairs if v > threshold))}

        if "how many" in q and "below" in q:
            threshold = float(re.search(r'below\s+(\d+)', q).group(1))
            return {"output": str(sum(1 for _, v in pairs if v < threshold))}

        # Default: highest
        return {"output": max(pairs, key=lambda x: x[1])[0]}

    # ── LEVEL 4: NUMBER LIST ──────────────────────────────────────────────────
    list_match = re.search(r'[Nn]umbers?[:\s]+([\d,\s]+)', query)
    if list_match:
        raw = re.split(r'[^\d,\s]', list_match.group(1))[0]
        nums = [int(n) for n in re.findall(r'\d+', raw)]
        if nums:
            if re.search(r'sum\s+even', q):
                return {"output": str(sum(n for n in nums if n % 2 == 0))}
            if re.search(r'sum\s+odd', q):
                return {"output": str(sum(n for n in nums if n % 2 != 0))}
            if "sum" in q:
                return {"output": str(sum(nums))}
            if "max" in q or "maximum" in q or "largest" in q:
                return {"output": str(max(nums))}
            if "min" in q or "minimum" in q or "smallest" in q:
                return {"output": str(min(nums))}
            if "average" in q or "mean" in q:
                avg = sum(nums) / len(nums)
                return {"output": str(int(avg) if avg == int(avg) else round(avg, 2))}
            if "sort" in q and ("desc" in q or "descending" in q):
                return {"output": ", ".join(str(n) for n in sorted(nums, reverse=True))}
            if "sort" in q:
                return {"output": ", ".join(str(n) for n in sorted(nums))}
            return {"output": str(sum(nums))}

    # ── LEVEL 3: PARITY ───────────────────────────────────────────────────────
    parity = re.search(r'is\s+(-?\d+)\s+(odd|even)', q)
    if parity:
        num = int(parity.group(1))
        kind = parity.group(2)
        if kind == "even":
            return {"output": "YES" if num % 2 == 0 else "NO"}
        return {"output": "YES" if num % 2 != 0 else "NO"}

    # ── LEVEL 2: DATE ─────────────────────────────────────────────────────────
    date = re.search(
        r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
        query, re.IGNORECASE
    )
    if date:
        return {"output": date.group(0)}

    # ── ARITHMETIC ────────────────────────────────────────────────────────────
    arith = re.search(r'(-?\d+)\s*([+\-*/])\s*(-?\d+)', query)
    if arith:
        a, op, b = int(arith.group(1)), arith.group(2), int(arith.group(3))
        if op == '+': return {"output": str(a + b)}
        if op == '-': return {"output": str(a - b)}
        if op == '*': return {"output": str(a * b)}
        if op == '/' and b != 0:
            r = a / b
            return {"output": str(int(r) if r == int(r) else round(r, 2))}

    return {"output": "0"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
