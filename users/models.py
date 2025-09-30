from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Adds profile picture, bio, and timestamps.
    """
    profile_picture = models.ImageField(
        upload_to='user_profiles/',
        blank=True,
        null=True,
        help_text="User's profile picture"
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text="User's biography or description"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

    @property
    def display_name(self):
        """Return the user's display name (first name + last name or username)"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username

    def get_character_count(self):
        """Return the number of characters this user has created"""
        return self.characters.count()
