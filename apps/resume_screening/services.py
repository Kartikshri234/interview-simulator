"""
Resume Screening — core services
Handles: file text extraction, TF-IDF similarity, Claude AI deep analysis
"""
import json
import os
from typing import Any, cast

import anthropic
import fitz          # PyMuPDF
import docx as python_docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ── Text extraction ───────────────────────────────────────────────────────────

def _extract_pdf(path: str) -> str:
    parts = []
    pdf = fitz.open(path)
    for page in pdf:
        text = page.get_text("text")
        parts.append(text if isinstance(text, str) else "")
    return " ".join(parts)


def _extract_docx(path: str) -> str:
    doc = python_docx.Document(path)
    return " ".join(p.text for p in doc.paragraphs)


def extract_resume_text(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".pdf"):
        return _extract_pdf(path)
    if lower.endswith(".docx"):
        return _extract_docx(path)
    return ""


# ── TF-IDF similarity ─────────────────────────────────────────────────────────

def compute_similarity(job_desc: str, resume_text: str) -> float:
    """Return cosine similarity (0-100) between job description and resume."""
    if not job_desc.strip() or not resume_text.strip():
        return 0.0
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([job_desc, resume_text])
    dense = cast(Any, vectors).toarray()
    score = cosine_similarity(dense[0:1], dense[1:2])
    return round(float(score[0][0]) * 100, 2)


# ── Claude AI deep analysis ───────────────────────────────────────────────────

_AI_PROMPT = """You are a senior HR analyst. Analyse the resume below against the job description and return ONLY a valid JSON object — no markdown, no preamble.

Job Description:
{job_desc}

Resume ({filename}):
{resume_text}

Return this exact JSON structure:
{{
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "gaps": ["<gap 1>", "<gap 2>"],
  "recommendation": "<1-2 sentence hiring recommendation>",
  "keywords_matched": ["<kw1>", "<kw2>", "<kw3>"],
  "keywords_missing": ["<kw1>", "<kw2>"]
}}"""


def ai_analyse_resume(job_desc: str, resume_text: str, filename: str) -> dict:
    """Call Claude claude-sonnet-4-20250514 to analyse a single resume against the JD."""
    try:
        client = anthropic.Anthropic()
        prompt = _AI_PROMPT.format(
            job_desc=job_desc[:3000],
            filename=filename,
            resume_text=resume_text[:3000],
        )
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw: str = message.content[0].text.strip()
        # Strip ```json ... ``` fences if present
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as exc:
        return {
            "strengths": [],
            "gaps": [],
            "recommendation": f"AI analysis unavailable: {exc}",
            "keywords_matched": [],
            "keywords_missing": [],
        }
