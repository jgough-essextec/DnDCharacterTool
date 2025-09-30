"""
Character app URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import viewsets
from . import utility_views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'characters', viewsets.CharacterViewSet, basename='character')

# Utility endpoints
utility_patterns = [
    # Dice rolling endpoints
    path('dice/roll/', utility_views.roll_dice, name='utility_roll_dice'),
    path('dice/ability-scores/', utility_views.roll_ability_scores, name='utility_roll_ability_scores'),
    path('dice/advantage/', utility_views.roll_with_advantage, name='utility_roll_advantage'),

    # Validation endpoints
    path('validate/character/<int:character_id>/', utility_views.validate_character, name='utility_validate_character'),
    path('validate/dice/', utility_views.validate_dice_notation, name='utility_validate_dice'),

    # Recommendation endpoints
    path('recommendations/classes/', utility_views.get_class_recommendations, name='utility_class_recommendations'),
    path('recommendations/build/<str:class_name>/', utility_views.get_build_recommendations, name='utility_build_recommendations'),

    # Analysis endpoints
    path('analyze/character/<int:character_id>/', utility_views.analyze_character_build, name='utility_analyze_character'),

    # Generation endpoints
    path('generate/name/', utility_views.generate_character_name, name='utility_generate_name'),
]

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # Utility endpoints under /utility/
    path('utility/', include(utility_patterns)),
]