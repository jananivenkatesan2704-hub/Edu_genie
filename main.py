"""EduGenie - Gemini powered learning assistant (FastAPI)."""
import os
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
load_dotenv(ROOT / ".env")

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_client: Optional[genai.Client] = None

app = FastAPI(title="EduGenie", version="1.0.0")

SYSTEM = (
    "You are EduGenie, a friendly, accurate and encouraging learning assistant. "
    "Use clear Markdown: short paragraphs, ## headings, bullet lists, **bold** for key terms. "
    "Be concise but complete. If you are unsure about something, say so."
)


def get_client() -> genai.Client:
    global _client
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your_key":
        raise HTTPException(500, "GEMINI_API_KEY is not set. Add it to your .env file and restart the server.")
    if _client is None:
        _client = genai.Client(api_key=key)
    return _client


def generate(prompt: str, temperature: float = 0.7) -> dict:
    client = get_client()
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM, temperature=temperature),
        )
    except HTTPException:
        raise
    except Exception as exc:  # network, quota, invalid key, etc.
        msg = str(exc)
        if "API key" in msg or "API_KEY" in msg or "401" in msg or "403" in msg:
            raise HTTPException(401, "Gemini rejected the API key. Check GEMINI_API_KEY in .env.")
        if "429" in msg or "quota" in msg.lower():
            raise HTTPException(429, "Gemini rate limit reached. Wait a moment and try again.")
        raise HTTPException(502, f"Gemini request failed: {msg[:300]}")
    text = (resp.text or "").strip()
    if not text:
        raise HTTPException(502, "Gemini returned an empty response. Try rephrasing your input.")
    return {"result": text, "model": MODEL}


class AskIn(BaseModel):
    question: str = Field(..., min_length=2, max_length=4000)


class ExplainIn(BaseModel):
    concept: str = Field(..., min_length=2, max_length=1000)


class QuizIn(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500)
    num_questions: Literal[3, 5, 7, 10] = 5
    difficulty: Literal["Easy", "Medium", "Hard"] = "Medium"


class PathIn(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500)
    level: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"
    duration: str = Field(..., min_length=2, max_length=100)


class SummarizeIn(BaseModel):
    text: str = Field(..., min_length=20, max_length=30000)


@app.get("/api/health")
def health():
    return {"status": "ok", "model": MODEL, "api_key_configured": bool(os.getenv("GEMINI_API_KEY", "").strip() not in ("", "your_key"))}


@app.post("/api/ask")
def ask(body: AskIn):
    return generate(f"Answer this student's question clearly and accurately, with an example where helpful:\n\n{body.question}")


@app.post("/api/explain")
def explain(body: ExplainIn):
    return generate(
        f"Explain the concept \"{body.concept}\" to a complete beginner. Use exactly these sections:\n"
        "## Simple Explanation\n(plain language, no jargon, use an analogy)\n"
        "## Example\n(one concrete, relatable example)\n"
        "## Key Points\n(4-6 bullet points)"
    )


@app.post("/api/quiz")
def quiz(body: QuizIn):
    return generate(
        f"Create a {body.difficulty} difficulty multiple-choice quiz on \"{body.topic}\" with exactly {body.num_questions} questions.\n"
        "Format each question as:\n"
        "### Question N\n(question text)\n\n- A) ...\n- B) ...\n- C) ...\n- D) ...\n\n"
        "**Answer:** X) correct option\n**Why:** one-sentence explanation\n\n"
        "Exactly one option must be correct. Vary the position of correct answers.",
        temperature=0.8,
    )


@app.post("/api/learning-path")
def learning_path(body: PathIn):
    return generate(
        f"Create a structured learning roadmap for \"{body.topic}\" for a {body.level} learner over {body.duration}.\n"
        "Include: ## Goal, then a breakdown by week/phase (## headings) with topics, practice activities and a milestone each, "
        "then ## Recommended Resources (types of resources, not made-up links) and ## Tips for Staying on Track. "
        f"The plan must realistically fit within {body.duration}."
    )


@app.post("/api/summarize")
def summarize(body: SummarizeIn):
    return generate(
        "Summarize the following educational text. Output:\n## Summary\n(2-3 sentences)\n## Key Points\n(5-8 bullets)\n"
        "## Key Terms\n(bullets: term - short definition)\nOnly use information from the text.\n\n"
        f"TEXT:\n{body.text}",
        temperature=0.3,
    )


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND), name="frontend")
