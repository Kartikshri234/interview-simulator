# REST API URLs
from django.urls import path
from .api_views import (
    SessionListCreateView, SessionDetailView,
    StartSessionView, EndSessionView,
    SubmitAnswerView, SubmitVoiceView, FacialAnalysisView,
)

urlpatterns = [
    path('sessions/',                          SessionListCreateView.as_view(), name='api-sessions'),
    path('sessions/<int:pk>/',                 SessionDetailView.as_view(),     name='api-session-detail'),
    path('sessions/<int:pk>/start/',           StartSessionView.as_view(),      name='api-session-start'),
    path('sessions/<int:pk>/end/',             EndSessionView.as_view(),        name='api-session-end'),
    path('sessions/<int:session_pk>/answer/',  SubmitAnswerView.as_view(),      name='api-submit-answer'),
    path('sessions/<int:session_pk>/voice/',   SubmitVoiceView.as_view(),       name='api-submit-voice'),
    path('answers/<int:answer_pk>/facial/',    FacialAnalysisView.as_view(),    name='api-facial'),
]
