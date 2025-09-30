"""
Game Content ViewSets for D&D Character Creator API
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch

from .models import (
    Skill, Language, Feat, Species, SpeciesTrait,
    DnDClass, ClassFeature, Subclass, Background,
    Equipment, Weapon, Armor, Spell
)
from .serializers import (
    SkillSerializer, LanguageSerializer, FeatSerializer,
    SpeciesSerializer, DnDClassSerializer, BackgroundSerializer,
    EquipmentSerializer, WeaponSerializer, ArmorSerializer,
    SpellSerializer
)


class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for D&D Skills.
    Provides list and detail views for the 18 core skills.
    """
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['associated_ability']
    search_fields = ['name', 'description']
    ordering = ['name']


class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for D&D Languages.
    """
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['rarity']
    search_fields = ['name', 'typical_speakers']
    ordering = ['name']


class FeatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for D&D 2024 Feats.
    """
    queryset = Feat.objects.all()
    serializer_class = FeatSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['feat_type', 'repeatable']
    search_fields = ['name', 'description']
    ordering = ['feat_type', 'name']


class SpeciesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for D&D Species with their traits.
    """
    serializer_class = SpeciesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['size']
    search_fields = ['name', 'description']
    ordering = ['name']

    def get_queryset(self):
        """Optimize with prefetched traits"""
        return Species.objects.prefetch_related('traits')


class DnDClassViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for D&D Classes with features and subclasses.
    """
    serializer_class = DnDClassSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['primary_ability', 'difficulty', 'hit_die']
    search_fields = ['name', 'description']
    ordering = ['name']

    def get_queryset(self):
        """Optimize with prefetched features and subclasses"""
        return DnDClass.objects.prefetch_related(
            Prefetch('features', queryset=ClassFeature.objects.order_by('level_acquired', 'name')),
            'subclasses'
        )


class BackgroundViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for D&D Backgrounds.
    """
    queryset = Background.objects.select_related('origin_feat')
    serializer_class = BackgroundSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['origin_feat']
    search_fields = ['name', 'description']
    ordering = ['name']


class EquipmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for general Equipment.
    """
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['equipment_type']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'cost_gp', 'weight']
    ordering = ['equipment_type', 'name']


class WeaponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for Weapons.
    """
    queryset = Weapon.objects.all()
    serializer_class = WeaponSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['weapon_category', 'damage_type']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'cost_gp', 'damage_dice']
    ordering = ['weapon_category', 'name']


class ArmorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for Armor.
    """
    queryset = Armor.objects.all()
    serializer_class = ArmorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['armor_type', 'stealth_disadvantage']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'base_ac', 'cost_gp']
    ordering = ['armor_type', 'name']


class SpellViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for Spells with advanced filtering.
    """
    serializer_class = SpellSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['spell_level', 'school', 'concentration', 'ritual', 'available_to_classes']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'spell_level']
    ordering = ['spell_level', 'name']

    def get_queryset(self):
        """Optimize with prefetched class relationships"""
        return Spell.objects.prefetch_related('available_to_classes')