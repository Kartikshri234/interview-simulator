from django.contrib.auth.models import AbstractUser
from django.db import models


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
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    @property
    def initials(self):
        return (self.username or self.email)[0].upper()
