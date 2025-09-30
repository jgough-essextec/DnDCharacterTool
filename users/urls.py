"""
Authentication URLs for D&D Character Creator
"""
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='user_register'),
    path('change-password/', views.PasswordChangeView.as_view(), name='change_password'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
]