"""
Utility API Views

Provides utility endpoints for:
- Dice rolling
- Character validation
- Recommendations
- Name generation
- Build analysis
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Character
from .services import (
    DiceRollerService,
    CharacterValidationService,
    RecommendationService,
    DiceRoll,
    AdvantageRoll
)


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow anonymous dice rolling
def roll_dice(request):
    """
    Roll dice using standard notation

    POST /api/utility/dice/roll/
    Body: {
        "notation": "3d6+2",  # required
        "description": "Damage roll"  # optional
    }

    Returns: {
        "dice_count": 3,
        "dice_size": 6,
        "modifier": 2,
        "individual_rolls": [4, 2, 6],
        "total": 14,
        "description": "3d6+2"
    }
    """
    notation = request.data.get('notation')
    description = request.data.get('description', '')

    if not notation:
        return Response(
            {'error': 'Dice notation is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Validate notation first
        if not DiceRollerService.validate_dice_notation(notation):
            return Response(
                {'error': f'Invalid dice notation: {notation}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Roll the dice
        result = DiceRollerService.parse_dice_notation(notation)

        # Override description if provided
        if description:
            result.description = description

        return Response({
            'dice_count': result.dice_count,
            'dice_size': result.dice_size,
            'modifier': result.modifier,
            'individual_rolls': result.individual_rolls,
            'total': result.total,
            'description': result.description
        })

    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def roll_ability_scores(request):
    """
    Roll ability scores using 4d6 drop lowest

    POST /api/utility/dice/ability-scores/
    Body: {
        "method": "roll",  # optional, defaults to "roll"
        "count": 6         # optional, defaults to 6
    }

    Returns: {
        "method": "roll",
        "scores": {
            "strength": {"rolls": [4, 3, 6, 2], "total": 13},
            "dexterity": {"rolls": [5, 6, 4, 1], "total": 15},
            ...
        },
        "statistics": {
            "total": 78,
            "average": 13.0,
            "highest": 16,
            "lowest": 10
        }
    }
    """
    method = request.data.get('method', 'roll')
    count = request.data.get('count', 6)

    if method != 'roll':
        return Response(
            {'error': 'Only "roll" method supported for this endpoint'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not isinstance(count, int) or count < 1 or count > 6:
        return Response(
            {'error': 'Count must be between 1 and 6'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Roll ability scores
        if count == 6:
            scores_dict = DiceRollerService.roll_standard_ability_scores()
        else:
            abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
            rolls = DiceRollerService.roll_ability_scores(count)
            scores_dict = dict(zip(abilities[:count], rolls))

        # Format response
        scores_response = {}
        totals = []

        for ability, roll in scores_dict.items():
            scores_response[ability] = {
                'rolls': roll.individual_rolls,
                'total': roll.total
            }
            totals.append(roll.total)

        statistics = {
            'total': sum(totals),
            'average': round(sum(totals) / len(totals), 1),
            'highest': max(totals),
            'lowest': min(totals)
        }

        return Response({
            'method': method,
            'scores': scores_response,
            'statistics': statistics
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def roll_with_advantage(request):
    """
    Roll with advantage, disadvantage, or normal

    POST /api/utility/dice/advantage/
    Body: {
        "advantage_type": "advantage",  # "advantage", "disadvantage", "normal"
        "modifier": 5,                  # optional
        "description": "Attack roll"    # optional
    }

    Returns: {
        "roll1": 15,
        "roll2": 8,
        "result": 20,
        "advantage_type": "advantage",
        "description": "Attack roll (Advantage)"
    }
    """
    advantage_type = request.data.get('advantage_type', 'normal')
    modifier = request.data.get('modifier', 0)
    description = request.data.get('description', 'Roll')

    if advantage_type not in ['advantage', 'disadvantage', 'normal']:
        return Response(
            {'error': 'advantage_type must be "advantage", "disadvantage", or "normal"'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        result = DiceRollerService.roll_with_advantage(
            sides=20,
            modifier=modifier,
            advantage_type=advantage_type
        )

        # Override description if provided
        if description != 'Roll':
            result.description = f"{description} ({result.description})"

        return Response({
            'roll1': result.roll1,
            'roll2': result.roll2,
            'result': result.result,
            'advantage_type': result.advantage_type,
            'description': result.description
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_character(request, character_id):
    """
    Validate a character against D&D rules

    POST /api/utility/validate/character/<id>/

    Returns: {
        "is_valid": true,
        "errors": {},
        "warnings": {}
    }
    """
    try:
        character = get_object_or_404(
            Character.objects.select_related('dnd_class', 'species', 'background', 'abilities'),
            id=character_id,
            user=request.user
        )

        # Run full validation
        errors = CharacterValidationService.validate_complete_character(character)
        warnings = CharacterValidationService.get_character_warnings(character)
        is_valid = len(errors) == 0

        return Response({
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'character_name': character.character_name or 'Unnamed Character'
        })

    except Character.DoesNotExist:
        return Response(
            {'error': 'Character not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def get_class_recommendations(request):
    """
    Get class recommendations based on playstyle preferences

    POST /api/utility/recommendations/classes/
    Body: {
        "playstyles": ["damage_dealer", "spellcaster"],
        "experience_level": "beginner"  # optional
    }

    Returns: {
        "primary": ["Fighter", "Barbarian"],
        "secondary": ["Paladin", "Ranger"],
        "descriptions": {...}
    }
    """
    playstyles = request.data.get('playstyles', [])
    experience_level = request.data.get('experience_level', 'beginner')

    if not isinstance(playstyles, list) or len(playstyles) == 0:
        return Response(
            {'error': 'playstyles must be a non-empty list'},
            status=status.HTTP_400_BAD_REQUEST
        )

    valid_playstyles = [
        'damage_dealer', 'spellcaster', 'support', 'tank',
        'sneaky', 'versatile', 'beginner_friendly'
    ]

    invalid_playstyles = [p for p in playstyles if p not in valid_playstyles]
    if invalid_playstyles:
        return Response(
            {'error': f'Invalid playstyles: {invalid_playstyles}. Valid options: {valid_playstyles}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        recommendations = RecommendationService.recommend_classes_by_playstyle(
            playstyles, experience_level
        )

        return Response({
            'primary': recommendations['primary'],
            'secondary': recommendations['secondary'],
            'playstyles_analyzed': playstyles,
            'experience_level': experience_level
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_build_recommendations(request, class_name):
    """
    Get comprehensive build recommendations for a class

    GET /api/utility/recommendations/build/<class_name>/

    Returns: {
        "class_name": "Fighter",
        "background_recommendations": ["Soldier", "Noble"],
        "species_recommendations": ["Human", "Dwarf"],
        "ability_priorities": {...},
        "feat_recommendations": [...],
        "spell_recommendations": [...]  # for spellcasters
    }
    """
    try:
        background_recs = RecommendationService.recommend_background_for_class(class_name)
        species_recs = RecommendationService.recommend_species_for_class(class_name)
        ability_priorities = RecommendationService.recommend_ability_score_priority(class_name)

        # Create a dummy character to get feat recommendations
        from .models import Character
        from game_content.models import DnDClass

        try:
            dnd_class = DnDClass.objects.get(name=class_name)
            dummy_character = Character(dnd_class=dnd_class, level=1)
            feat_recs = RecommendationService.recommend_feats_for_build(dummy_character)
        except DnDClass.DoesNotExist:
            feat_recs = []

        # Get spell recommendations for spellcasters
        spell_recs = []
        if dnd_class and dnd_class.spellcaster:
            spell_recs = RecommendationService.recommend_spells_for_class(class_name, 1, 0)  # Cantrips
            spell_recs.extend(RecommendationService.recommend_spells_for_class(class_name, 1, 1))  # 1st level

        return Response({
            'class_name': class_name,
            'background_recommendations': background_recs,
            'species_recommendations': species_recs,
            'ability_priorities': ability_priorities,
            'feat_recommendations': feat_recs,
            'spell_recommendations': spell_recs
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_character_build(request, character_id):
    """
    Analyze character build for optimization and synergies

    POST /api/utility/analyze/character/<id>/

    Returns: {
        "optimization_score": {...},
        "synergy_analysis": {...},
        "suggestions": [...]
    }
    """
    try:
        character = get_object_or_404(
            Character.objects.select_related('dnd_class', 'species', 'background', 'abilities'),
            id=character_id,
            user=request.user
        )

        # Get optimization score
        optimization = RecommendationService.get_build_optimization_score(character)

        # Get synergy analysis
        synergies = RecommendationService.analyze_character_synergies(character)

        # Get ability score assignment recommendations
        suggestions = []
        if hasattr(character, 'abilities'):
            current_scores = [
                character.abilities.strength_score,
                character.abilities.dexterity_score,
                character.abilities.constitution_score,
                character.abilities.intelligence_score,
                character.abilities.wisdom_score,
                character.abilities.charisma_score
            ]

            optimal_assignment = RecommendationService.recommend_ability_score_assignment(
                character.dnd_class.name, current_scores
            )

            suggestions.append({
                'type': 'ability_scores',
                'current_assignment': {
                    'strength': character.abilities.strength_score,
                    'dexterity': character.abilities.dexterity_score,
                    'constitution': character.abilities.constitution_score,
                    'intelligence': character.abilities.intelligence_score,
                    'wisdom': character.abilities.wisdom_score,
                    'charisma': character.abilities.charisma_score
                },
                'optimal_assignment': optimal_assignment
            })

        return Response({
            'optimization_score': optimization,
            'synergy_analysis': synergies,
            'suggestions': suggestions,
            'character_name': character.character_name or 'Unnamed Character'
        })

    except Character.DoesNotExist:
        return Response(
            {'error': 'Character not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def generate_character_name(request):
    """
    Generate a random character name

    POST /api/utility/generate/name/
    Body: {
        "species": "Human",      # optional
        "gender": "any",         # "male", "female", "any"
        "count": 1               # optional, 1-10
    }

    Returns: {
        "names": ["Aerdyn"],
        "species": "Human",
        "gender": "any"
    }
    """
    species = request.data.get('species', 'Human')
    gender = request.data.get('gender', 'any')
    count = request.data.get('count', 1)

    if not isinstance(count, int) or count < 1 or count > 10:
        return Response(
            {'error': 'count must be between 1 and 10'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        names = []
        for _ in range(count):
            name = DiceRollerService.generate_character_name(species, gender)
            names.append(name)

        return Response({
            'names': names,
            'species': species,
            'gender': gender,
            'count': len(names)
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def validate_dice_notation(request):
    """
    Validate dice notation without rolling

    POST /api/utility/validate/dice/
    Body: {
        "notation": "3d6+2"
    }

    Returns: {
        "valid": true,
        "notation": "3d6+2"
    }
    """
    notation = request.data.get('notation')

    if not notation:
        return Response(
            {'error': 'Dice notation is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        is_valid = DiceRollerService.validate_dice_notation(notation)

        return Response({
            'valid': is_valid,
            'notation': notation
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )