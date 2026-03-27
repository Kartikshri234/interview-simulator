# HTML page views — Django templates
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from .models import InterviewSession, InterviewAnswer, BookmarkedQuestion


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
    trend_qs = (
        sessions
        .filter(status='completed', overall_score__isnull=False)
        .order_by('created_at')[:10]
    )
    # Windows-safe date formatting (%-d is Linux-only)
    trend_labels  = [s.created_at.strftime('%d %b').lstrip('0') for s in trend_qs]
    trend_scores  = [round(s.overall_score, 1) for s in trend_qs]

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

    # ── Feature 11: Smart topic recommendations ─────────────────
    recommendation = None
    if cat_qs:
        # Find category with lowest avg score (at least 1 session)
        worst = sorted(cat_qs, key=lambda c: c['avg'])
        if worst:
            rec_cat = worst[0]['category']
            rec_avg = round(worst[0]['avg'], 1)
            recommendation = {'category': rec_cat, 'avg': rec_avg}
    # ────────────────────────────────────────────────────────────

    # ── Feature 16: Streak ──────────────────────────────────────
    streak = getattr(request.user, 'daily_streak', 0)
    # ────────────────────────────────────────────────────────────

    return render(request, 'interview/dashboard.html', {
        'stats': stats, 'recent': recent,
        'chart_data': chart_data,
        'recommendation': recommendation,
        'streak': streak,
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

    # Aggregate emotion data across all answers for Feature 14 (emotion heatmap)
    emotion_totals = {}
    emotion_count  = 0
    for answer in answers:
        if answer.face_emotions:
            for emotion, value in answer.face_emotions.items():
                emotion_totals[emotion] = emotion_totals.get(emotion, 0) + value
            emotion_count += 1
    avg_emotions = {}
    if emotion_count:
        avg_emotions = {k: round(v / emotion_count, 1) for k, v in emotion_totals.items()}

    # ── Feature 15: Voice analytics aggregate ───────────────────
    voice_stats = None
    answers_with_voice = [a for a in answers if a.voice_analytics]
    if answers_with_voice:
        total_wpm   = sum(a.voice_analytics.get('wpm', 0) for a in answers_with_voice)
        total_filler = sum(a.voice_analytics.get('filler_count', 0) for a in answers_with_voice)
        voice_stats = {
            'avg_wpm': round(total_wpm / len(answers_with_voice), 1),
            'total_fillers': total_filler,
        }
    # ────────────────────────────────────────────────────────────

    return render(request, 'interview/results.html', {
        'session': session,
        'answers': answers,
        'avg_emotions': avg_emotions,
        'avg_emotions_json': json.dumps(avg_emotions),
        'voice_stats': voice_stats,
    })


@login_required
def history(request):
    sessions = InterviewSession.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'interview/history.html', {'sessions': sessions})


@login_required
def bookmarks(request):
    bmarks = BookmarkedQuestion.objects.filter(user=request.user).select_related('session').order_by('-created_at')
    return render(request, 'interview/bookmarks.html', {'bookmarks': bmarks})
