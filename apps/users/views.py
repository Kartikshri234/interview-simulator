# HTML page views — rendered by Django templates
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Q
from .models import CustomUser


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid email or password.')
    return render(request, 'users/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip()
        password  = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        target    = request.POST.get('target_role', '').strip()
        exp       = request.POST.get('experience_level', 'mid')

        if not username or not email or not password:
            messages.error(request, 'All fields are required.')
        elif password != password2:
            messages.error(request, 'Passwords do not match.')
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        elif CustomUser.objects.filter(username__iexact=username).exists():
            messages.error(request, 'That username is already taken.')
        elif CustomUser.objects.filter(email__iexact=email).exists():
            messages.error(request, 'An account with that email already exists.')
        else:
            user = CustomUser.objects.create_user(
                username=username, email=email, password=password,
                target_role=target, experience_level=exp,
            )
            login(request, user)
            messages.success(request, f'Welcome, {username}! Your account is ready.')
            return redirect('dashboard')
    return render(request, 'users/register.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        u = request.user
        new_username = request.POST.get('username', u.username).strip()
        # Check username uniqueness on profile update (exclude current user)
        if new_username != u.username and CustomUser.objects.filter(username__iexact=new_username).exclude(pk=u.pk).exists():
            messages.error(request, 'That username is already taken.')
            return redirect('profile')
        u.username         = new_username
        u.bio              = request.POST.get('bio', u.bio).strip()
        u.target_role      = request.POST.get('target_role', u.target_role).strip()
        u.experience_level = request.POST.get('experience_level', u.experience_level)
        if request.FILES.get('avatar'):
            u.avatar = request.FILES['avatar']
        u.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    from apps.interview.models import InterviewSession
    stats = InterviewSession.objects.filter(user=request.user).aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        avg_score=Avg('overall_score'),
    )
    return render(request, 'users/profile.html', {'stats': stats})
