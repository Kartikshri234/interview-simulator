"""
Resume Screening — Django view
GET  /resume-screening/ → render form
POST /resume-screening/ → process resumes, render results
"""
import os
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from werkzeug.utils import secure_filename

from .services import extract_resume_text, compute_similarity, ai_analyse_resume

UPLOAD_DIR = os.path.join(settings.BASE_DIR, "resume_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}


def _safe_name(original: str) -> str:
    """Return a filesystem-safe filename, preserving extension."""
    try:
        name = secure_filename(original)
        return name if name else "resume"
    except Exception:
        return "resume"


@login_required
def resume_screening(request):
    results = []
    job_desc = ""

    if request.method == "POST":
        job_desc = request.POST.get("job_description", "").strip()
        use_ai   = request.POST.get("use_ai") == "true"
        files    = request.FILES.getlist("resumes")

        for uploaded_file in files:
            original_name = uploaded_file.name or ""
            _, ext = os.path.splitext(original_name.lower())
            if ext not in ALLOWED_EXTENSIONS:
                continue

            safe_name = _safe_name(original_name)
            file_path = os.path.join(UPLOAD_DIR, safe_name)

            # Save to disk
            with open(file_path, "wb+") as dest:
                for chunk in uploaded_file.chunks():
                    dest.write(chunk)

            resume_text = extract_resume_text(file_path)
            score       = compute_similarity(job_desc, resume_text)

            result = {
                "name":        safe_name,
                "score":       score,
                "ai_analysis": None,
            }

            if use_ai and resume_text and job_desc:
                result["ai_analysis"] = ai_analyse_resume(job_desc, resume_text, safe_name)

            results.append(result)

        # Rank highest first
        results.sort(key=lambda r: r["score"], reverse=True)

    return render(request, "resume_screening/screening.html", {
        "results":  results,
        "job_desc": job_desc,
    })
