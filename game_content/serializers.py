"""
Serializers for Game Content API
"""
from rest_framework import serializers
from .models import (
    Skill, Language, Feat, Species, SpeciesTrait,
    DnDClass, ClassFeature, Subclass, Background,
    Equipment, Weapon, Armor, Spell
)


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for D&D Skills"""
    class Meta:
        model = Skill
        fields = ['id', 'name', 'associated_ability', 'description']


class LanguageSerializer(serializers.ModelSerializer):
    """Serializer for D&D Languages"""
    class Meta:
        model = Language
        fields = ['id', 'name', 'script', 'typical_speakers', 'rarity']


class FeatSerializer(serializers.ModelSerializer):
    """Serializer for D&D Feats"""
    class Meta:
        model = Feat
        fields = [
            'id', 'name', 'feat_type', 'description', 'repeatable',
            'prerequisites', 'ability_score_increase', 'benefits'
        ]


class SpeciesTraitSerializer(serializers.ModelSerializer):
    """Serializer for Species Traits"""
    class Meta:
        model = SpeciesTrait
        fields = ['id', 'name', 'trait_type', 'description', 'mechanical_effect']


class SpeciesSerializer(serializers.ModelSerializer):
    """Serializer for D&D Species with nested traits"""
    traits = SpeciesTraitSerializer(many=True, read_only=True)

    class Meta:
        model = Species
        fields = [
            'id', 'name', 'description', 'size', 'speed',
            'darkvision_range', 'languages', 'traits'
        ]


class ClassFeatureSerializer(serializers.ModelSerializer):
    """Serializer for Class Features"""
    class Meta:
        model = ClassFeature
        fields = [
            'id', 'name', 'level_acquired', 'description',
            'feature_type', 'uses_per_rest', 'choice_options'
        ]


class SubclassSerializer(serializers.ModelSerializer):
    """Serializer for Subclasses"""
    class Meta:
        model = Subclass
        fields = ['id', 'name', 'description', 'level_available']


class DnDClassSerializer(serializers.ModelSerializer):
    """Serializer for D&D Classes with nested features and subclasses"""
    features = ClassFeatureSerializer(many=True, read_only=True)
    subclasses = SubclassSerializer(many=True, read_only=True)

    class Meta:
        model = DnDClass
        fields = [
            'id', 'name', 'description', 'primary_ability', 'hit_die', 'difficulty',
            'armor_proficiencies', 'weapon_proficiencies', 'saving_throw_proficiencies',
            'skill_proficiency_count', 'skill_proficiency_choices',
            'features', 'subclasses'
        ]


class BackgroundSerializer(serializers.ModelSerializer):
    """Serializer for D&D Backgrounds"""
    origin_feat = FeatSerializer(read_only=True)

    class Meta:
        model = Background
        fields = [
            'id', 'name', 'description', 'origin_feat',
            'skill_proficiencies', 'tool_proficiencies', 'languages',
            'equipment_options', 'starting_gold'
        ]


class EquipmentSerializer(serializers.ModelSerializer):
    """Serializer for general Equipment"""
    class Meta:
        model = Equipment
        fields = [
            'id', 'name', 'equipment_type', 'cost_gp', 'weight',
            'description', 'properties'
        ]


class WeaponSerializer(serializers.ModelSerializer):
    """Serializer for Weapons"""
    class Meta:
        model = Weapon
        fields = [
            'id', 'name', 'equipment_type', 'cost_gp', 'weight',
            'description', 'properties', 'weapon_category',
            'damage_dice', 'damage_type', 'range_normal', 'range_long',
            'mastery_property'
        ]


class ArmorSerializer(serializers.ModelSerializer):
    """Serializer for Armor"""
    class Meta:
        model = Armor
        fields = [
            'id', 'name', 'equipment_type', 'cost_gp', 'weight',
            'description', 'properties', 'armor_type', 'base_ac',
            'dex_bonus_limit', 'strength_requirement', 'stealth_disadvantage'
        ]


class SpellSerializer(serializers.ModelSerializer):
    """Serializer for Spells"""
    available_to_classes = DnDClassSerializer(many=True, read_only=True)
    components_display = serializers.ReadOnlyField()

    class Meta:
        model = Spell
        fields = [
            'id', 'name', 'spell_level', 'school', 'casting_time',
            'range', 'duration', 'concentration', 'ritual',
            'components_v', 'components_s', 'components_m', 'material_components',
            'components_display', 'description', 'higher_level_description',
            'available_to_classes'
        ]


# Compact serializers for references
class SkillSummarySerializer(serializers.ModelSerializer):
    """Compact skill serializer for references"""
    class Meta:
        model = Skill
        fields = ['id', 'name', 'associated_ability']


class ClassSummarySerializer(serializers.ModelSerializer):
    """Compact class serializer for references"""
    class Meta:
        model = DnDClass
        fields = ['id', 'name', 'primary_ability', 'hit_die']


class SpeciesSummarySerializer(serializers.ModelSerializer):
    """Compact species serializer for references"""
    class Meta:
        model = Species
        fields = ['id', 'name', 'size', 'speed']


class BackgroundSummarySerializer(serializers.ModelSerializer):
    """Compact background serializer for references"""
    class Meta:
        model = Background
        fields = ['id', 'name']


class EquipmentSummarySerializer(serializers.ModelSerializer):
    """Compact equipment serializer for references"""
    class Meta:
        model = Equipment
        fields = ['id', 'name', 'equipment_type']


class SpellSummarySerializer(serializers.ModelSerializer):
    """Compact spell serializer for references"""
    class Meta:
        model = Spell
        fields = ['id', 'name', 'spell_level', 'school']