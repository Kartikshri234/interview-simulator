from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.users.jwt_utils import RateLimitedTokenObtainPairView, RateLimitedTokenRefreshView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # JWT auth endpoints — rate-limited, custom claims
    path('api/auth/token/',         RateLimitedTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', RateLimitedTokenRefreshView.as_view(),    name='token_refresh'),

    # REST API
    path('api/users/',     include('apps.users.api_urls')),
    path('api/interview/', include('apps.interview.api_urls')),

    # Django HTML pages
    path('', include('apps.users.urls')),
    path('', include('apps.interview.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
