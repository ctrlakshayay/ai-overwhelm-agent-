from dotenv import load_dotenv
load_dotenv()

import os
import json
import logging
from fastapi import FastAPI
from pydantic import BaseModel, Field
from groq import AsyncGroq

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Agent API",
    description="A production-ready AI agent API.",
    version="1.0.0"
)

# Initialize Groq Client
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

# Request model
class SolveRequest(BaseModel):
    input: str = Field(..., description="The problem to solve")

# Response model
class SolveResponse(BaseModel):
    result: str
    method: str
    confidence: float

# Health check
@app.get("/")
async def health_check():
    return {"status": "ok"}

# Main endpoint
@app.post("/solve", response_model=SolveResponse)
async def solve_problem(request: SolveRequest):

    fallback_response = SolveResponse(
        result="Could not process accurately",
        method="fallback",
        confidence=0.5
    )

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """You are a fast AI agent. Return ONLY valid JSON, no extra text, no markdown.
Format: {"result": "string", "method": "Math | Coding | Logic | General", "confidence": number}"""
                },
                {
                    "role": "user",
                    "content": f"Problem:\n{request.input}"
                }
            ],
            temperature=0,
            max_tokens=200,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content

        if not content:
            logger.warning("Empty response from LLM")
            return fallback_response

        try:
            parsed_data = json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {content}")
            return fallback_response

        return SolveResponse(
            result=str(parsed_data.get("result", fallback_response.result)),
            method=str(parsed_data.get("method", fallback_response.method)),
            confidence=float(parsed_data.get("confidence", fallback_response.confidence))
        )

    except Exception as e:
        logger.error(f"Error processing request: {type(e).__name__}: {e}")
        return fallback_response