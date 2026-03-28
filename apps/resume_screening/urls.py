# HTML page URLs for resume screening
from django.urls import path
from .views import resume_screening

urlpatterns = [
    path('resume-screening/', resume_screening, name='resume_screening'),
]
