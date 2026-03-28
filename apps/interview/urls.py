# HTML page URLs
from django.urls import path
from .views import dashboard, new_interview, interview_room, results, history, bookmarks, home

urlpatterns = [
    path('',                              home,            name='home'),
    path('dashboard/',                    dashboard,       name='dashboard'),
    path('interview/new/',                new_interview,   name='new_interview'),
    path('interview/<int:session_id>/',   interview_room,  name='interview_room'),
    path('results/<int:session_id>/',     results,         name='results'),
    path('history/',                      history,         name='history'),
    path('bookmarks/',                    bookmarks,       name='bookmarks'),
]
