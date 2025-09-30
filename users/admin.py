from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced User admin with custom fields"""

    # Fields to display in the list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined', 'get_character_count')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    # Add our custom fields to the user form
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('profile_picture', 'bio', 'created_at', 'updated_at')
        }),
    )

    # Fields to show when creating a new user
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('profile_picture', 'bio')
        }),
    )

    # Make timestamp fields read-only
    readonly_fields = ('created_at', 'updated_at', 'date_joined', 'last_login')

    def get_character_count(self, obj):
        """Display character count for each user"""
        return obj.get_character_count()
    get_character_count.short_description = 'Characters'
