from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    target_role = models.CharField(max_length=120, blank=True, help_text='e.g. Backend Engineer')
    experience_level = models.CharField(
        max_length=10,
        choices=[('junior', 'Junior'), ('mid', 'Mid-level'), ('senior', 'Senior')],
        default='mid',
    )
    # Feature 16: Daily streak
    daily_streak  = models.IntegerField(default=0)
    last_active   = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    @property
    def initials(self):
        return (self.username or self.email)[0].upper()

    def update_streak(self):
        """Call after each session completion or daily login."""
        today = timezone.now().date()
        if self.last_active is None:
            self.daily_streak = 1
        elif self.last_active == today:
            return  # already updated today
        elif (today - self.last_active).days == 1:
            self.daily_streak += 1
        else:
            self.daily_streak = 1
        self.last_active = today
        self.save(update_fields=['daily_streak', 'last_active'])
