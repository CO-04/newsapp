from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser, extending the built-in UserAdmin."""

    list_display  = ('username', 'email', 'role', 'is_staff')
    list_filter   = ('role', 'is_staff', 'is_active')
    fieldsets     = UserAdmin.fieldsets + (
        ('Role & Profile', {'fields': ('role', 'bio')}),
        ('Subscriptions', {
            'fields': (
                'subscribed_publishers',
                'subscribed_journalists',
            ),
        }),
    )
