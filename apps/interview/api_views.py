from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .ai_services import (
    analyze_face_base64,
    analyze_sentiment,
    evaluate_answer,
    generate_questions,
    generate_summary,
    transcribe_audio,
)
from .models import InterviewAnswer, InterviewSession


# In-memory runtime state for active sessions (sufficient for local/dev usage).
SESSION_RUNTIME_STATE = {}


class InterviewSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewSession
        fields = (
            "id",
            "title",
            "category",
            "difficulty",
            "status",
            "total_questions",
            "overall_score",
            "confidence_score",
            "sentiment_score",
            "readiness",
            "created_at",
            "started_at",
            "ended_at",
        )
        read_only_fields = (
            "id",
            "status",
            "overall_score",
            "confidence_score",
            "sentiment_score",
            "readiness",
            "created_at",
            "started_at",
            "ended_at",
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
    state = SESSION_RUNTIME_STATE.get(session.id)
    if state:
        return state

    count = max(1, int(session.total_questions or 5))
    questions = generate_questions(session.category, session.difficulty, count)
    if not questions:
        questions = generate_questions("python", "medium", count)

    state = {"questions": questions, "index": 0}
    SESSION_RUNTIME_STATE[session.id] = state
    return state


def _finalize_session(session: InterviewSession):
    answers_qs = session.answers.all()
    if not answers_qs.exists():
        session.status = "completed"
        session.ended_at = timezone.now()
        session.overall_score = 0.0
        session.confidence_score = 0.0
        session.sentiment_score = 0.0
        session.feedback_summary = "Session ended without submitted answers."
        session.improvement_tips = ["Attempt each question before ending the interview."]
        session.strengths = ["Session was started"]
        session.readiness = "Not Ready"
        session.save()
        return

    avg_score = round(answers_qs.aggregate(v=Avg("score"))["v"] or 0.0, 1)
    avg_conf = round(answers_qs.aggregate(v=Avg("confidence_score"))["v"] or 0.0, 1)
    avg_sent = round(answers_qs.aggregate(v=Avg("sentiment_score"))["v"] or 0.0, 3)

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
    session.readiness = summary.get("readiness", "")
    session.save()


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
            return Response({"question": "No questions available."})

        q = questions[idx]
        return Response({
            "question": q.get("question_text", ""),
            "question_text": q.get("question_text", ""),
            "index": idx + 1,
            "total": len(questions),
        })


class EndSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        session = get_object_or_404(InterviewSession, pk=pk, user=request.user)
        _finalize_session(session)
        SESSION_RUNTIME_STATE.pop(session.id, None)
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
            SESSION_RUNTIME_STATE.pop(session.id, None)
            return Response({"completed": True})

        current = questions[idx]
        question_text = current.get("question_text", "")
        expected_keywords = current.get("expected_keywords", [])

        eval_data = evaluate_answer(question_text, answer_text, expected_keywords)
        sentiment = analyze_sentiment(answer_text)

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
        )

        state["index"] = idx + 1
        if state["index"] >= len(questions):
            _finalize_session(session)
            SESSION_RUNTIME_STATE.pop(session.id, None)
            return Response({"completed": True})

        next_question = questions[state["index"]].get("question_text", "")
        return Response({
            "completed": False,
            "next_question": next_question,
            "index": state["index"] + 1,
            "total": len(questions),
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
        eval_data = evaluate_answer(question_text, transcribed, expected_keywords)
        sentiment = analyze_sentiment(transcribed)

        answer.transcribed_text = transcribed
        answer.answer_text = transcribed
        answer.score = eval_data.get("score") or 0
        answer.confidence_score = eval_data.get("confidence_score") or sentiment.get("confidence_score") or 0
        answer.sentiment = sentiment.get("sentiment") or "neutral"
        answer.sentiment_score = sentiment.get("score") or 0
        answer.keywords_matched = eval_data.get("keywords_matched") or []
        answer.ai_feedback = eval_data.get("ai_feedback") or ""
        answer.improvement_suggestions = eval_data.get("improvement_suggestions") or ""
        answer.save()

        return Response({
            "answer_id": answer.id,
            "transcribed_text": transcribed,
            "score": answer.score,
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
        answer.confidence_score = answer.confidence_score or 0
        answer.save(update_fields=["face_emotions", "confidence_score"])

        return Response({
            "dominant_emotion": result.get("dominant_emotion", "neutral"),
            "emotions": answer.face_emotions,
        })
