import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import httpx

app = FastAPI()

class SolveRequest(BaseModel):
    query: str
    assets: Optional[List[str]] = []

@app.get("/")
async def health():
    return {"status": "ok"}

@app.post("/solve")
async def solve(request: SolveRequest):
    query = request.query

    system_prompt = """You are an answer extraction engine. 
Return ONLY the final answer — no explanation, no sentence, no punctuation unless the answer itself requires it.

Rules:
- If asked who scored highest/best/most/won → return ONLY the name e.g. "Bob"
- If asked who scored lowest/worst/least → return ONLY the name e.g. "Alice"  
- If asked for a number (sum, difference, average, total, max, min) → return ONLY the number e.g. "10"
- If asked yes/no (is X even/odd) → return ONLY "YES" or "NO"
- If asked for a date → return ONLY the date
- Never return a sentence. Never explain. Just the bare answer."""

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.environ.get("ANTHROPIC_API_KEY", ""),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 50,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": query}
                ]
            }
        )
        data = response.json()
        answer = data["content"][0]["text"].strip()
        return {"output": answer}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
