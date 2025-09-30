"""
Character ViewSets for D&D Character Creator API
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch

from .models import Character
from .serializers import (
    CharacterListSerializer,
    CharacterDetailSerializer,
    CharacterCreateSerializer
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a character to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the character.
        return obj.user == request.user


class CharacterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Character management with step-by-step creation support.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['character_state', 'dnd_class', 'species', 'level', 'is_complete']
    ordering = ['-last_modified_date']

    def get_queryset(self):
        """Return characters for the current user with optimized queries"""
        return Character.objects.filter(
            user=self.request.user
        ).select_related(
            'dnd_class', 'subclass', 'background', 'species', 'abilities', 'details'
        ).prefetch_related(
            'skills', 'equipment', 'spells', 'feats', 'languages'
        )

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return CharacterListSerializer
        elif self.action == 'create':
            return CharacterCreateSerializer
        else:
            return CharacterDetailSerializer

    def perform_create(self, serializer):
        """Set the character owner to the current user"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Create a copy of an existing character"""
        character = self.get_object()

        # Create a duplicate with modified name
        duplicate_name = f"{character.character_name} (Copy)"
        duplicate = Character.objects.create(
            user=request.user,
            character_name=duplicate_name,
            dnd_class=character.dnd_class,
            subclass=character.subclass,
            background=character.background,
            species=character.species,
            alignment=character.alignment,
            level=character.level,
            character_state='draft'  # Always start as draft
        )

        # Copy abilities if they exist
        if hasattr(character, 'abilities'):
            duplicate.abilities = character.abilities
            duplicate.abilities.pk = None
            duplicate.abilities.character = duplicate
            duplicate.abilities.save()

        serializer = CharacterDetailSerializer(duplicate, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def finalize(self, request, pk=None):
        """Mark a character as complete"""
        character = self.get_object()
        character.is_complete = True
        character.character_state = 'complete'
        character.save()

        serializer = CharacterDetailSerializer(character, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def sheet(self, request, pk=None):
        """Get character data formatted for character sheet display"""
        character = self.get_object()

        # Use the detail serializer but could create a specialized one later
        serializer = CharacterDetailSerializer(character, context={'request': request})
        return Response({
            'character': serializer.data,
            'calculated_stats': {
                'proficiency_bonus': character.calculate_proficiency_bonus(),
                'ability_modifiers': {
                    'strength': character.abilities.strength_modifier if hasattr(character, 'abilities') else 0,
                    'dexterity': character.abilities.dexterity_modifier if hasattr(character, 'abilities') else 0,
                    'constitution': character.abilities.constitution_modifier if hasattr(character, 'abilities') else 0,
                    'intelligence': character.abilities.intelligence_modifier if hasattr(character, 'abilities') else 0,
                    'wisdom': character.abilities.wisdom_modifier if hasattr(character, 'abilities') else 0,
                    'charisma': character.abilities.charisma_modifier if hasattr(character, 'abilities') else 0,
                }
            }
        })

    # Step-specific update endpoints
    @action(detail=True, methods=['put', 'patch'], url_path='class')
    def update_class(self, request, pk=None):
        """Update character's class and subclass"""
        character = self.get_object()

        if 'dnd_class' in request.data:
            character.dnd_class_id = request.data['dnd_class']
        if 'subclass' in request.data:
            character.subclass_id = request.data['subclass']

        character.save()
        serializer = CharacterDetailSerializer(character, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['put', 'patch'], url_path='background')
    def update_background(self, request, pk=None):
        """Update character's background"""
        character = self.get_object()
        character.background_id = request.data.get('background')
        character.save()

        serializer = CharacterDetailSerializer(character, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['put', 'patch'], url_path='species')
    def update_species(self, request, pk=None):
        """Update character's species"""
        character = self.get_object()
        character.species_id = request.data.get('species')
        character.save()

        serializer = CharacterDetailSerializer(character, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['put', 'patch'], url_path='ability-scores')
    def update_ability_scores(self, request, pk=None):
        """Update character's ability scores"""
        character = self.get_object()

        # Get or create abilities
        abilities, created = character.abilities.get_or_create(character=character)

        # Update ability scores if provided
        for ability in ['strength_score', 'dexterity_score', 'constitution_score',
                       'intelligence_score', 'wisdom_score', 'charisma_score']:
            if ability in request.data:
                setattr(abilities, ability, request.data[ability])

        abilities.save()

        serializer = CharacterDetailSerializer(character, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['put', 'patch'], url_path='alignment')
    def update_alignment(self, request, pk=None):
        """Update character's alignment"""
        character = self.get_object()
        character.alignment = request.data.get('alignment', '')
        character.save()

        serializer = CharacterDetailSerializer(character, context={'request': request})
        return Response(serializer.data)