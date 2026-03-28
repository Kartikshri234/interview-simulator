import random
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .ai_services import (
    analyze_face_base64,
    analyze_sentiment,
    analyze_voice,
    evaluate_answer,
    generate_questions,
    generate_summary,
    transcribe_audio,
)
from .models import BookmarkedQuestion, InterviewAnswer, InterviewSession


# In-memory runtime state for active sessions.
# NOTE: This resets on every server restart/deploy. Sessions mid-flight
# during a redeploy will regenerate questions from scratch on next API call.
SESSION_RUNTIME_STATE = {}

ALL_CATEGORIES = [
    'python', 'django', 'dsa', 'system_design',
    'behavioral', 'javascript', 'database', 'devops', 'ml',
]


class InterviewSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewSession
        fields = (
            "id", "title", "category", "difficulty", "session_type",
            "status", "total_questions", "overall_score",
            "confidence_score", "sentiment_score", "readiness",
            "recommended_topics", "created_at", "started_at", "ended_at",
        )
        read_only_fields = (
            "id", "status", "overall_score", "confidence_score",
            "sentiment_score", "readiness", "recommended_topics",
            "created_at", "started_at", "ended_at",
        )


class SessionListCreateView(generics.ListCreateAPIView):
    serializer_class = InterviewSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InterviewSession.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status="pending")


class SessionDetailView(generics.RetrieveAPIView):
    serializer_class = InterviewSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InterviewSession.objects.filter(user=self.request.user)


def _ensure_runtime_state(session: InterviewSession):
    state = SESSION_RUNTIME_STATE.get(session.pk)
    if state:
        return state

    count = max(1, int(session.total_questions or 5))

    if session.session_type == 'mock':
        categories = ALL_CATEGORIES.copy()
        random.shuffle(categories)
        questions = []
        per_cat = max(1, count // len(categories))
        remaining = count
        for cat in categories:
            if remaining <= 0:
                break
            n = min(per_cat, remaining)
            qs = generate_questions(cat, session.difficulty, n)
            questions.extend(qs[:n])
            remaining -= n
        random.shuffle(questions)
    else:
        questions = generate_questions(session.category, session.difficulty, count)
        if not questions:
            questions = generate_questions("python", "medium", count)

    # Determine current index from already-answered questions
    answered_count = InterviewAnswer.objects.filter(session=session).count()
    index = min(answered_count, len(questions))

    state = {"questions": questions, "index": index}
    SESSION_RUNTIME_STATE[session.pk] = state
    return state


def _finalize_session(session: InterviewSession):
    answers_qs = InterviewAnswer.objects.filter(session=session)
    if not answers_qs.exists():
        session.status = "completed"
        session.ended_at = timezone.now()
        session.overall_score = 0.0
        session.confidence_score = 0.0
        session.sentiment_score = 0.0
        session.feedback_summary = "Session ended without submitted answers."
        session.improvement_tips = ["Attempt each question before ending the interview."]
        session.strengths = ["Session was started"]
        session.recommended_topics = []
        session.readiness = "Not Ready"
        session.save()
        _update_streak(session.user)
        return

    avg_score = round(answers_qs.aggregate(v=Avg("score"))["v"] or 0.0, 1)
    avg_conf  = round(answers_qs.aggregate(v=Avg("confidence_score"))["v"] or 0.0, 1)
    avg_sent  = round(answers_qs.aggregate(v=Avg("sentiment_score"))["v"] or 0.0, 3)

    summary_payload = {
        "category": session.category,
        "difficulty": session.difficulty,
        "total_questions": answers_qs.count(),
        "average_score": avg_score,
        "answers": [
            {
                "question": a.question_text,
                "score": a.score,
                "sentiment": a.sentiment,
                "feedback": a.ai_feedback,
            }
            for a in answers_qs.order_by("answered_at")
        ],
    }
    summary = generate_summary(summary_payload)

    session.status = "completed"
    session.ended_at = timezone.now()
    session.overall_score = avg_score
    session.confidence_score = avg_conf
    session.sentiment_score = avg_sent
    session.feedback_summary = summary.get("overall_feedback", "")
    session.improvement_tips = summary.get("improvement_areas", [])
    session.strengths = summary.get("strengths", [])
    session.recommended_topics = summary.get("recommended_topics", [])
    session.readiness = summary.get("readiness", "")
    session.save()

    _update_streak(session.user)


def _update_streak(user):
    try:
        user.update_streak()
    except Exception:
        pass


class StartSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        session = get_object_or_404(InterviewSession, pk=pk, user=request.user)
        if session.status == "completed":
            return Response({"detail": "Session is already completed."}, status=400)

        if not session.started_at:
            session.started_at = timezone.now()
        session.status = "active"
        session.save(update_fields=["started_at", "status"])

        state = _ensure_runtime_state(session)
        idx = state.get("index", 0)
        questions = state.get("questions", [])
        if idx >= len(questions):
            return Response({"detail": "No questions available.", "question": ""}, status=400)

        q = questions[idx]
        return Response({
            "question": q.get("question_text", ""),
            "question_text": q.get("question_text", ""),
            "index": idx + 1,
            "total": len(questions),
            "time_limit_seconds": q.get("time_limit_seconds", 120),
        })


class EndSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        session = get_object_or_404(InterviewSession, pk=pk, user=request.user)
        if session.status != "completed":
            _finalize_session(session)
        SESSION_RUNTIME_STATE.pop(session.pk, None)
        return Response({"detail": "Session ended.", "status": session.status})


class SubmitAnswerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_pk):
        session = get_object_or_404(InterviewSession, pk=session_pk, user=request.user)
        if session.status == "completed":
            return Response({"detail": "Session already completed."}, status=400)

        answer_text = (request.data.get("answer_text") or "").strip()
        if not answer_text:
            return Response({"detail": "answer_text is required."}, status=400)

        state = _ensure_runtime_state(session)
        idx = state.get("index", 0)
        questions = state.get("questions", [])

        if idx >= len(questions):
            _finalize_session(session)
            SESSION_RUNTIME_STATE.pop(session.pk, None)
            return Response({"completed": True})

        current = questions[idx]
        question_text     = current.get("question_text", "")
        expected_keywords = current.get("expected_keywords", [])
        ideal_outline     = current.get("ideal_answer_outline", "")

        eval_data = evaluate_answer(question_text, answer_text, expected_keywords)
        sentiment = analyze_sentiment(answer_text)
        voice_data = analyze_voice(answer_text)

        InterviewAnswer.objects.create(
            session=session,
            question_text=question_text,
            answer_text=answer_text,
            score=eval_data.get("score") or 0,
            confidence_score=eval_data.get("confidence_score") or sentiment.get("confidence_score") or 0,
            sentiment=sentiment.get("sentiment") or "neutral",
            sentiment_score=sentiment.get("score") or 0,
            keywords_matched=eval_data.get("keywords_matched") or [],
            ai_feedback=eval_data.get("ai_feedback") or "",
            improvement_suggestions=eval_data.get("improvement_suggestions") or "",
            voice_analytics=voice_data,
        )

        state["index"] = idx + 1

        # Always include ideal answer and keywords in every response
        base_response = {
            "ideal_answer_outline": ideal_outline,
            "expected_keywords": expected_keywords,
            "score": eval_data.get("score") or 0,
            "ai_feedback": eval_data.get("ai_feedback") or "",
        }

        if state["index"] >= len(questions):
            _finalize_session(session)
            SESSION_RUNTIME_STATE.pop(session.pk, None)
            return Response({**base_response, "completed": True})

        next_q = questions[state["index"]]
        return Response({
            **base_response,
            "completed": False,
            "next_question": next_q.get("question_text", ""),
            "index": state["index"] + 1,
            "total": len(questions),
            "time_limit_seconds": next_q.get("time_limit_seconds", 120),
        })


class SubmitVoiceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_pk):
        session = get_object_or_404(InterviewSession, pk=session_pk, user=request.user)
        audio_file = request.FILES.get("audio_file")
        if not audio_file:
            return Response({"detail": "audio_file is required."}, status=400)

        question_text = (request.data.get("question_text") or "Interview question").strip()
        expected_keywords = request.data.get("expected_keywords") or []
        if isinstance(expected_keywords, str):
            expected_keywords = [k.strip() for k in expected_keywords.split(",") if k.strip()]

        answer = InterviewAnswer.objects.create(
            session=session,
            question_text=question_text,
            audio_file=audio_file,
        )

        transcribed = transcribe_audio(answer.audio_file.path)
        eval_data   = evaluate_answer(question_text, transcribed, expected_keywords)
        sentiment   = analyze_sentiment(transcribed)
        voice_data  = analyze_voice(transcribed)

        answer.transcribed_text        = transcribed
        answer.answer_text             = transcribed
        answer.score                   = eval_data.get("score") or 0
        answer.confidence_score        = eval_data.get("confidence_score") or sentiment.get("confidence_score") or 0
        answer.sentiment               = sentiment.get("sentiment") or "neutral"
        answer.sentiment_score         = sentiment.get("score") or 0
        answer.keywords_matched        = eval_data.get("keywords_matched") or []
        answer.ai_feedback             = eval_data.get("ai_feedback") or ""
        answer.improvement_suggestions = eval_data.get("improvement_suggestions") or ""
        answer.voice_analytics         = voice_data
        answer.save()

        return Response({
            "answer_id": answer.pk,
            "transcribed_text": transcribed,
            "score": answer.score,
            "voice_analytics": voice_data,
        })


class FacialAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, answer_pk):
        answer = get_object_or_404(
            InterviewAnswer,
            pk=answer_pk,
            session__user=request.user,
        )

        image_b64 = request.data.get("image_base64")
        if not image_b64:
            return Response({"detail": "image_base64 is required."}, status=400)

        result = analyze_face_base64(image_b64)
        answer.face_emotions = result.get("emotions") or {}
        answer.save(update_fields=["face_emotions"])

        return Response({
            "dominant_emotion": result.get("dominant_emotion", "neutral"),
            "emotions": answer.face_emotions,
        })


# ── Feature 7: Bookmark endpoints ──────────────────────────────

class BookmarkListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        bmarks = BookmarkedQuestion.objects.filter(user=request.user).order_by('-created_at')
        data = [
            {
                'id': b.pk,
                'question_text': b.question_text,
                'session_id': b.session_id,
                'note': b.note,
                'created_at': b.created_at.isoformat(),
            }
            for b in bmarks
        ]
        return Response(data)


class BookmarkCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, session_pk):
        session = get_object_or_404(InterviewSession, pk=session_pk, user=request.user)
        question_text = (request.data.get("question_text") or "").strip()
        note          = (request.data.get("note") or "").strip()
        if not question_text:
            return Response({"detail": "question_text is required."}, status=400)

        bmark, created = BookmarkedQuestion.objects.get_or_create(
            user=request.user,
            session=session,
            question_text=question_text,
            defaults={'note': note},
        )
        return Response({
            "id": bmark.pk,
            "created": created,
            "question_text": bmark.question_text,
        }, status=201 if created else 200)


class BookmarkDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        bmark = get_object_or_404(BookmarkedQuestion, pk=pk, user=request.user)
        bmark.delete()
        return Response({"detail": "Bookmark removed."})


# ── Feature 11: Smart topic recommendation ─────────────────────

class RecommendationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models import Avg, Count
        cat_qs = (
            InterviewSession.objects
            .filter(user=request.user, status='completed', overall_score__isnull=False)
            .values('category')
            .annotate(avg=Avg('overall_score'), count=Count('id'))
            .order_by('avg')
        )
        if not cat_qs:
            return Response({'recommendation': None, 'reason': 'Complete at least one session first.'})

        worst = cat_qs[0]
        return Response({
            'recommendation': {
                'category': worst['category'],
                'avg_score': round(worst['avg'], 1),
                'sessions': worst['count'],
            },
            'reason': f"Your weakest area is {worst['category']} with an average of {round(worst['avg'],1)}/10.",
        })


# ── Feature 12: Adaptive difficulty suggestion ─────────────────

class AdaptiveDifficultyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        category = request.query_params.get('category', 'python')
        from django.db.models import Avg
        result = (
            InterviewSession.objects
            .filter(user=request.user, category=category, status='completed', overall_score__isnull=False)
            .aggregate(avg=Avg('overall_score'))
        )
        avg = result.get('avg') or 0
        if avg >= 7.5:
            suggested = 'hard'
            reason = f'Your avg for {category} is {round(avg,1)}/10 — time to level up!'
        elif avg < 5:
            suggested = 'easy'
            reason = f'Your avg for {category} is {round(avg,1)}/10 — build the fundamentals first.'
        else:
            suggested = 'medium'
            reason = f'Your avg for {category} is {round(avg,1)}/10 — keep sharpening at medium.'
        return Response({'category': category, 'suggested_difficulty': suggested, 'avg_score': round(avg, 1), 'reason': reason})


# ── Feature 16: Streak info ─────────────────────────────────────

class StreakView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'daily_streak': getattr(user, 'daily_streak', 0),
            'last_active': str(getattr(user, 'last_active', None)),
        })
