import re
import math
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class SolveRequest(BaseModel):
    query: str
    assets: Optional[List[str]] = []

def extract_numbers(text):
    return [int(n) for n in re.findall(r'-?\d+', text)]

def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True

def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

@app.post("/solve")
async def solve_problem(request: SolveRequest):
    query = request.query
    q_low = query.lower()
    numbers = extract_numbers(query)

    # FIBONACCI
    if "fibonacci" in q_low:
        if numbers:
            return {"output": str(fibonacci(numbers[0]))}

    # FACTORIAL
    if "factorial" in q_low:
        if numbers:
            return {"output": str(math.factorial(numbers[0]))}

    # PRIME CHECK
    if "prime" in q_low and ("is" in q_low or "?" in query):
        if numbers:
            return {"output": "YES" if is_prime(numbers[0]) else "NO"}

    # SQUARE ROOT
    if "square root" in q_low or "sqrt" in q_low:
        if numbers:
            result = math.isqrt(numbers[0])
            if result * result == numbers[0]:
                return {"output": str(result)}
            return {"output": str(round(math.sqrt(numbers[0]), 4))}

    # POWER / EXPONENT
    if any(k in q_low for k in ["power", "exponent", "^", "**"]):
        if len(numbers) >= 2:
            return {"output": str(numbers[0] ** numbers[1])}

    # SORT
    if "sort" in q_low or "order" in q_low:
        if numbers:
            if "desc" in q_low or "descend" in q_low or "largest first" in q_low:
                return {"output": ", ".join(str(n) for n in sorted(numbers, reverse=True))}
            else:
                return {"output": ", ".join(str(n) for n in sorted(numbers))}

    # MAX / MIN
    if any(k in q_low for k in ["largest", "maximum", "max", "greatest", "highest", "biggest"]):
        if numbers:
            return {"output": str(max(numbers))}
    if any(k in q_low for k in ["smallest", "minimum", "min", "lowest", "least"]):
        if numbers:
            return {"output": str(min(numbers))}

    # AVERAGE / MEAN
    if any(k in q_low for k in ["average", "mean"]):
        if numbers:
            avg = sum(numbers) / len(numbers)
            result = int(avg) if avg == int(avg) else round(avg, 4)
            return {"output": str(result)}

    # MODULO
    if any(k in q_low for k in ["modulo", "modulus", "remainder", "mod "]):
        if len(numbers) >= 2:
            return {"output": str(numbers[0] % numbers[1])}

    # SUMMATION (even/odd/all)
    if any(k in q_low for k in ["sum", "add", "total", "calculate"]):
        if numbers:
            if "even" in q_low:
                return {"output": str(sum(n for n in numbers if n % 2 == 0))}
            elif "odd" in q_low:
                return {"output": str(sum(n for n in numbers if n % 2 != 0))}
            else:
                return {"output": str(sum(numbers))}

    # MULTIPLY
    if any(k in q_low for k in ["multiply", "product", "times"]):
        if len(numbers) >= 2:
            result = 1
            for n in numbers:
                result *= n
            return {"output": str(result)}

    # DIVIDE
    if any(k in q_low for k in ["divide", "divided by"]):
        if len(numbers) >= 2:
            result = numbers[0] / numbers[1]
            result = int(result) if result == int(result) else round(result, 4)
            return {"output": str(result)}

    # SUBTRACT
    if any(k in q_low for k in ["subtract", "minus", "difference"]):
        if len(numbers) >= 2:
            return {"output": str(numbers[0] - numbers[1])}

    # ADDITION with plus
    if "plus" in q_low:
        if numbers:
            return {"output": str(sum(numbers))}

    # INLINE MATH EXPRESSION (e.g. "what is 15 + 27")
    math_expr = re.search(r'(\d+)\s*([\+\-\*\/])\s*(\d+)', query)
    if math_expr:
        a, op, b = int(math_expr.group(1)), math_expr.group(2), int(math_expr.group(3))
        if op == '+':
            return {"output": str(a + b)}
        elif op == '-':
            return {"output": str(a - b)}
        elif op == '*':
            return {"output": str(a * b)}
        elif op == '/' and b != 0:
            result = a / b
            result = int(result) if result == int(result) else round(result, 4)
            return {"output": str(result)}

    # PARITY CHECK (is X odd/even?)
    if numbers and ("odd" in q_low or "even" in q_low):
        num = numbers[0]
        if "odd" in q_low:
            return {"output": "YES" if num % 2 != 0 else "NO"}
        if "even" in q_low:
            return {"output": "YES" if num % 2 == 0 else "NO"}

    # COUNT NUMBERS
    if any(k in q_low for k in ["count", "how many number"]):
        if numbers:
            return {"output": str(len(numbers))}

    # STRING REVERSE
    if "reverse" in q_low:
        word_match = re.search(r'reverse\s+(?:the\s+)?(?:word\s+|string\s+)?["\']?([a-zA-Z0-9]+)["\']?', q_low)
        if word_match:
            return {"output": word_match.group(1)[::-1]}

    # STRING LENGTH
    if any(k in q_low for k in ["length", "characters", "how many char", "how many letter"]):
        str_match = re.search(r'["\'](.+?)["\']', query)
        if str_match:
            return {"output": str(len(str_match.group(1)))}

    # DATE EXTRACTION
    date_pattern = r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
    date_match = re.search(date_pattern, query, re.IGNORECASE)
    if date_match:
        return {"output": date_match.group(0)}

    # ABSOLUTE VALUE
    if "absolute" in q_low or "abs" in q_low:
        if numbers:
            return {"output": str(abs(numbers[0]))}

    # DEFAULT FALLBACK
    return {"output": "0"}
