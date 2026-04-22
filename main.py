from dotenv import load_dotenv
load_dotenv()

import os
import re
import math
import logging
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
from groq import AsyncGroq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Agent API", version="1.0.0")

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

class SolveRequest(BaseModel):
    query: str = Field(..., description="The question to answer")
    assets: Optional[List[str]] = Field(default=[], description="Asset URLs")

class SolveResponse(BaseModel):
    output: str

def solve_math(query: str):
    q = query.lower()
    numbers = re.findall(r'\d+\.?\d*', query)

    if len(numbers) == 1:
        n = int(float(numbers[0]))
        if 'factorial' in q:
            return f"The factorial is {math.factorial(n)}."
        if 'square root' in q or 'sqrt' in q:
            result = math.sqrt(n)
            return f"The square root is {int(result) if result.is_integer() else round(result, 2)}."

    if len(numbers) >= 2:
        a, b = float(numbers[0]), float(numbers[1])

        def fmt(x):
            return int(x) if isinstance(x, float) and x.is_integer() else round(x, 2)

        if any(w in q for w in ['sum', 'add', 'plus', '+']):
            return f"The sum is {fmt(a + b)}."
        if any(w in q for w in ['subtract', 'minus', 'difference', '-']):
            return f"The difference is {fmt(a - b)}."
        if any(w in q for w in ['multiply', 'product', 'times', '×', '*']):
            return f"The product is {fmt(a * b)}."
        if any(w in q for w in ['divide', 'quotient', '÷', '/']):
            if b != 0:
                return f"The quotient is {fmt(a / b)}."
        if any(w in q for w in ['power', 'exponent', '^', 'raised']):
            return f"The result is {fmt(a ** b)}."
        if 'average' in q or 'mean' in q:
            return f"The average is {fmt((a + b) / 2)}."
        if 'modulo' in q or 'remainder' in q or '%' in q:
            return f"The remainder is {fmt(a % b)}."

    return None

@app.get("/")
async def health_check():
    return {"status": "ok"}

@app.post("/solve", response_model=SolveResponse)
async def solve_problem(request: SolveRequest):
    try:
        # Try math first
        math_result = solve_math(request.query)
        if math_result:
            return SolveResponse(output=math_result)

        # Use LLM for everything else
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """Answer every question in exactly one short sentence ending with a period.
Be direct. No extra explanation, no bullet points, no formatting.
Examples:
- 'The capital of France is Paris.'
- 'Water boils at 100 degrees Celsius.'
- 'The speed of light is 299,792,458 meters per second.'"""
                },
                {
                    "role": "user",
                    "content": request.query
                }
            ],
            temperature=0,
            max_tokens=100
        )

        content = response.choices[0].message.content or "Could not process accurately"
        return SolveResponse(output=content)

    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {e}")
        return SolveResponse(output="Could not process accurately")