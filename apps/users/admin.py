from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display  = ('email', 'username', 'target_role', 'experience_level', 'created_at')
    search_fields = ('email', 'username')
    list_filter   = ('experience_level',)
