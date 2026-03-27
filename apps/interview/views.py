# HTML page views — Django templates
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from .models import InterviewSession, InterviewAnswer


@login_required
def dashboard(request):
    sessions = InterviewSession.objects.filter(user=request.user).order_by('-created_at')
    stats    = sessions.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        avg_score=Avg('overall_score'),
    )
    stats['avg_score'] = round(stats['avg_score'] or 0, 1)
    recent = sessions[:6]

    # ── Feature 4: Progress Charts ──────────────────────────────
    # Score trend: last 10 completed sessions (oldest first for chart)
    trend_qs = (
        sessions
        .filter(status='completed', overall_score__isnull=False)
        .order_by('created_at')[:10]
    )
    trend_labels  = [s.created_at.strftime('%-d %b') for s in trend_qs]
    trend_scores  = [round(s.overall_score, 1) for s in trend_qs]

    # Average score per category (completed only)
    cat_qs = (
        sessions
        .filter(status='completed', overall_score__isnull=False)
        .values('category')
        .annotate(avg=Avg('overall_score'), count=Count('id'))
        .order_by('-avg')
    )
    cat_labels = [c['category'].replace('_', ' ').title() for c in cat_qs]
    cat_scores = [round(c['avg'], 1) for c in cat_qs]
    cat_counts = [c['count'] for c in cat_qs]

    chart_data = json.dumps({
        'trend':  {'labels': trend_labels,  'scores': trend_scores},
        'topics': {'labels': cat_labels, 'scores': cat_scores, 'counts': cat_counts},
    })
    # ────────────────────────────────────────────────────────────

    return render(request, 'interview/dashboard.html', {
        'stats': stats, 'recent': recent,
        'chart_data': chart_data,
    })


@login_required
def new_interview(request):
    return render(request, 'interview/new_interview.html')


@login_required
def interview_room(request, session_id):
    session = get_object_or_404(InterviewSession, pk=session_id, user=request.user)
    if session.status == 'completed':
        return redirect('results', session_id=session_id)
    return render(request, 'interview/room.html', {'session': session})


@login_required
def results(request, session_id):
    session = get_object_or_404(InterviewSession, pk=session_id, user=request.user)
    answers = session.answers.all().order_by('answered_at')
    return render(request, 'interview/results.html', {'session': session, 'answers': answers})


@login_required
def history(request):
    sessions = InterviewSession.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'interview/history.html', {'sessions': sessions})
