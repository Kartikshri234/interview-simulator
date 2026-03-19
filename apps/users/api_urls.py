# REST API URLs for users
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .api_views import RegisterAPIView, ProfileAPIView, UserStatsAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(),  name='api-register'),
    path('profile/',  ProfileAPIView.as_view(),   name='api-profile'),
    path('stats/',    UserStatsAPIView.as_view(),  name='api-stats'),
]
