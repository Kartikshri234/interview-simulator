# REST API URLs
from django.urls import path
from .api_views import (
    SessionListCreateView, SessionDetailView,
    StartSessionView, EndSessionView,
    SubmitAnswerView, SubmitVoiceView, FacialAnalysisView,
    BookmarkListView, BookmarkCreateView, BookmarkDeleteView,
    RecommendationView, AdaptiveDifficultyView, StreakView,
)

urlpatterns = [
    path('sessions/',                          SessionListCreateView.as_view(), name='api-sessions'),
    path('sessions/<int:pk>/',                 SessionDetailView.as_view(),     name='api-session-detail'),
    path('sessions/<int:pk>/start/',           StartSessionView.as_view(),      name='api-session-start'),
    path('sessions/<int:pk>/end/',             EndSessionView.as_view(),        name='api-session-end'),
    path('sessions/<int:session_pk>/answer/',  SubmitAnswerView.as_view(),      name='api-submit-answer'),
    path('sessions/<int:session_pk>/voice/',   SubmitVoiceView.as_view(),       name='api-submit-voice'),
    path('sessions/<int:session_pk>/bookmark/', BookmarkCreateView.as_view(),   name='api-bookmark-create'),
    path('answers/<int:answer_pk>/facial/',    FacialAnalysisView.as_view(),    name='api-facial'),
    # Feature 7: bookmarks
    path('bookmarks/',                         BookmarkListView.as_view(),      name='api-bookmarks'),
    path('bookmarks/<int:pk>/delete/',         BookmarkDeleteView.as_view(),    name='api-bookmark-delete'),
    # Feature 11: recommendation
    path('recommend/',                         RecommendationView.as_view(),    name='api-recommend'),
    # Feature 12: adaptive difficulty
    path('adaptive-difficulty/',               AdaptiveDifficultyView.as_view(), name='api-adaptive'),
    # Feature 16: streak
    path('streak/',                            StreakView.as_view(),             name='api-streak'),
]
