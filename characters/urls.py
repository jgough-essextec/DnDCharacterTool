"""
Character app URLs
"""
from django.urls import path, include
# from rest_framework.routers import DefaultRouter

# from . import viewsets
# from . import utility_views
from . import frontend_views

# Create router and register viewsets - temporarily disabled
# router = DefaultRouter()
# router.register(r'characters', viewsets.CharacterViewSet, basename='character')

# Frontend URLs (HTML views)
frontend_patterns = [
    # Character list and management
    path('', frontend_views.CharacterListView.as_view(), name='character_list'),
    path('create/', frontend_views.character_create_wizard, name='character_create'),
    path('<int:character_id>/edit/', frontend_views.character_create_wizard, name='character_edit'),
    path('<int:character_id>/delete/', frontend_views.character_delete, name='character_delete'),
    path('<int:character_id>/duplicate/', frontend_views.character_duplicate, name='character_duplicate'),

    # Character creation wizard steps
    path('<int:character_id>/step/<int:step>/', frontend_views.character_create_step, name='character_create_step'),
    path('<int:character_id>/save-draft/', frontend_views.character_save_draft, name='character_save_draft'),

    # Character sheet view
    path('<int:character_id>/sheet/', frontend_views.character_sheet_view, name='character_sheet'),
]

# Utility endpoints (API) - temporarily disabled
# utility_patterns = [
#     # Dice rolling endpoints
#     path('dice/roll/', utility_views.roll_dice, name='utility_roll_dice'),
#     path('dice/ability-scores/', utility_views.roll_ability_scores, name='utility_roll_ability_scores'),
#     path('dice/advantage/', utility_views.roll_with_advantage, name='utility_roll_advantage'),
#
#     # Validation endpoints
#     path('validate/character/<int:character_id>/', utility_views.validate_character, name='utility_validate_character'),
#     path('validate/dice/', utility_views.validate_dice_notation, name='utility_validate_dice'),
#
#     # Recommendation endpoints
#     path('recommendations/classes/', utility_views.get_class_recommendations, name='utility_class_recommendations'),
#     path('recommendations/build/<str:class_name>/', utility_views.get_build_recommendations, name='utility_build_recommendations'),
#
#     # Analysis endpoints
#     path('analyze/character/<int:character_id>/', utility_views.analyze_character_build, name='utility_analyze_character'),
#
#     # Generation endpoints
#     path('generate/name/', utility_views.generate_character_name, name='utility_generate_name'),
# ]

urlpatterns = [
    # Frontend URLs (serve HTML)
    path('', include(frontend_patterns)),

    # API endpoints - temporarily disabled
    # path('api/', include(router.urls)),
    # path('api/utility/', include(utility_patterns)),
]