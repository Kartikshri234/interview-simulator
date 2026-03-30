from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from apps.users.jwt_utils import RateLimitedTokenObtainPairView, RateLimitedTokenRefreshView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # JWT auth endpoints
    path('api/auth/token/',         RateLimitedTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', RateLimitedTokenRefreshView.as_view(),    name='token_refresh'),

    # REST API
    path('api/users/',     include('apps.users.api_urls')),
    path('api/interview/', include('apps.interview.api_urls')),

    # HTML pages — order matters: specific apps first
    path('', include('apps.interview.urls')),
    path('', include('apps.users.urls')),
    path('', include('apps.resume_screening.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom 404 / 500 handlers
handler404 = 'config.views.handler404'
handler500 = 'config.views.handler500'
