"""
Core API URLs - Main API router for the D&D Character Creator
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Import viewsets from other apps (will create these next)
from game_content import viewsets as game_viewsets
from characters import viewsets as character_viewsets
from users import viewsets as user_viewsets

# Create the main API router
router = DefaultRouter()

# User management
router.register(r'users', user_viewsets.UserViewSet, basename='user')

# Game Content
router.register(r'classes', game_viewsets.DnDClassViewSet, basename='dndclass')
router.register(r'species', game_viewsets.SpeciesViewSet, basename='species')
router.register(r'backgrounds', game_viewsets.BackgroundViewSet, basename='background')
router.register(r'feats', game_viewsets.FeatViewSet, basename='feat')
router.register(r'skills', game_viewsets.SkillViewSet, basename='skill')
router.register(r'languages', game_viewsets.LanguageViewSet, basename='language')
router.register(r'equipment', game_viewsets.EquipmentViewSet, basename='equipment')
router.register(r'weapons', game_viewsets.WeaponViewSet, basename='weapon')
router.register(r'armor', game_viewsets.ArmorViewSet, basename='armor')
router.register(r'spells', game_viewsets.SpellViewSet, basename='spell')

# Characters
router.register(r'characters', character_viewsets.CharacterViewSet, basename='character')

# API URL patterns
urlpatterns = [
    # Authentication endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/', include('users.urls')),  # Additional auth endpoints

    # Characters app URLs (includes utility endpoints)
    path('', include('characters.urls')),

    # API versioning - include all router URLs under v1
    path('v1/', include(router.urls)),
    path('v1/', include('characters.urls')),

    # API root (latest version defaults to v1)
    path('', include(router.urls)),
]