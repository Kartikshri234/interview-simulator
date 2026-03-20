# REST API URLs for users
from django.urls import path
from .api_views import (
    RegisterAPIView,
    ProfileAPIView,
    LogoutAPIView,
    ChangePasswordAPIView,
    UserStatsAPIView,
)

urlpatterns = [
    path('register/',        RegisterAPIView.as_view(),       name='api-register'),
    path('profile/',         ProfileAPIView.as_view(),        name='api-profile'),
    path('stats/',           UserStatsAPIView.as_view(),      name='api-stats'),
    path('change-password/', ChangePasswordAPIView.as_view(), name='api-change-password'),
    # Logout (blacklists refresh token)
    path('logout/',          LogoutAPIView.as_view(),         name='api-logout'),
]
