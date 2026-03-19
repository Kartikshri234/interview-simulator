# HTML page views — Django templates
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
    return render(request, 'interview/dashboard.html', {'stats': stats, 'recent': recent})


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
