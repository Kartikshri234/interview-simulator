from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # JWT token endpoints
    path('api/auth/token/',         TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(),    name='token_refresh'),

    # REST API
    path('api/users/',     include('apps.users.api_urls')),
    path('api/interview/', include('apps.interview.api_urls')),

    # Django HTML pages
    path('', include('apps.users.urls')),
    path('', include('apps.interview.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
