"""
Serializers for Character API
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    Character, CharacterAbilities, CharacterSkill, CharacterSavingThrow,
    CharacterProficiency, CharacterEquipment, CharacterSpell,
    CharacterFeature, CharacterFeat, CharacterLanguage, CharacterDetails
)
from game_content.serializers import (
    ClassSummarySerializer, SpeciesSummarySerializer, BackgroundSummarySerializer,
    SkillSummarySerializer, EquipmentSummarySerializer, SpellSummarySerializer
)

User = get_user_model()


class CharacterAbilitiesSerializer(serializers.ModelSerializer):
    """Serializer for Character Abilities with calculated modifiers"""
    strength_modifier = serializers.ReadOnlyField()
    dexterity_modifier = serializers.ReadOnlyField()
    constitution_modifier = serializers.ReadOnlyField()
    intelligence_modifier = serializers.ReadOnlyField()
    wisdom_modifier = serializers.ReadOnlyField()
    charisma_modifier = serializers.ReadOnlyField()

    class Meta:
        model = CharacterAbilities
        fields = [
            'strength_score', 'dexterity_score', 'constitution_score',
            'intelligence_score', 'wisdom_score', 'charisma_score',
            'strength_modifier', 'dexterity_modifier', 'constitution_modifier',
            'intelligence_modifier', 'wisdom_modifier', 'charisma_modifier'
        ]


class CharacterDetailsSerializer(serializers.ModelSerializer):
    """Serializer for Character Details"""
    class Meta:
        model = CharacterDetails
        fields = [
            'age', 'height', 'weight', 'eyes', 'skin', 'hair', 'pronouns',
            'portrait_url', 'personality_traits', 'ideals', 'bonds', 'flaws',
            'backstory', 'notes'
        ]


class CharacterSkillSerializer(serializers.ModelSerializer):
    """Serializer for Character Skills with calculated bonus"""
    skill = SkillSummarySerializer(read_only=True)
    skill_id = serializers.IntegerField(write_only=True)
    bonus = serializers.ReadOnlyField()

    class Meta:
        model = CharacterSkill
        fields = ['skill', 'skill_id', 'proficiency_type', 'bonus']


class CharacterSavingThrowSerializer(serializers.ModelSerializer):
    """Serializer for Character Saving Throws with calculated bonus"""
    bonus = serializers.ReadOnlyField()

    class Meta:
        model = CharacterSavingThrow
        fields = ['ability_name', 'is_proficient', 'bonus']


class CharacterProficiencySerializer(serializers.ModelSerializer):
    """Serializer for Character Proficiencies"""
    class Meta:
        model = CharacterProficiency
        fields = ['proficiency_type', 'proficiency_name']


class CharacterEquipmentSerializer(serializers.ModelSerializer):
    """Serializer for Character Equipment"""
    equipment = EquipmentSummarySerializer(read_only=True)
    equipment_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CharacterEquipment
        fields = ['equipment', 'equipment_id', 'quantity', 'equipped', 'attuned']


class CharacterSpellSerializer(serializers.ModelSerializer):
    """Serializer for Character Spells"""
    spell = SpellSummarySerializer(read_only=True)
    spell_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CharacterSpell
        fields = ['spell', 'spell_id', 'always_prepared', 'prepared']


class CharacterFeatSerializer(serializers.ModelSerializer):
    """Serializer for Character Feats"""
    class Meta:
        model = CharacterFeat
        fields = ['feat', 'source', 'choice_made']


class CharacterLanguageSerializer(serializers.ModelSerializer):
    """Serializer for Character Languages"""
    class Meta:
        model = CharacterLanguage
        fields = ['language']


class CharacterListSerializer(serializers.ModelSerializer):
    """Compact serializer for character list view"""
    dnd_class = ClassSummarySerializer(read_only=True)
    species = SpeciesSummarySerializer(read_only=True)
    background = BackgroundSummarySerializer(read_only=True)
    level_display = serializers.ReadOnlyField()

    class Meta:
        model = Character
        fields = [
            'id', 'character_name', 'level', 'level_display',
            'dnd_class', 'species', 'background', 'character_state',
            'is_complete', 'last_modified_date'
        ]


class CharacterCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new character"""
    class Meta:
        model = Character
        fields = ['character_name']

    def create(self, validated_data):
        """Create a new character with default values"""
        character = Character.objects.create(
            character_state='draft',
            is_complete=False,
            **validated_data
        )

        # Create associated models
        CharacterAbilities.objects.create(character=character)
        CharacterDetails.objects.create(character=character)

        return character


class CharacterDetailSerializer(serializers.ModelSerializer):
    """Complete serializer for character detail view"""
    dnd_class = ClassSummarySerializer(read_only=True)
    species = SpeciesSummarySerializer(read_only=True)
    background = BackgroundSummarySerializer(read_only=True)
    abilities = CharacterAbilitiesSerializer(read_only=True)
    details = CharacterDetailsSerializer(read_only=True)
    skills = CharacterSkillSerializer(many=True, read_only=True)
    saving_throws = CharacterSavingThrowSerializer(many=True, read_only=True)
    proficiencies = CharacterProficiencySerializer(many=True, read_only=True)
    equipment = CharacterEquipmentSerializer(many=True, read_only=True)
    spells = CharacterSpellSerializer(many=True, read_only=True)
    feats = CharacterFeatSerializer(many=True, read_only=True)
    languages = CharacterLanguageSerializer(many=True, read_only=True)
    level_display = serializers.ReadOnlyField()

    # Write-only fields for updates
    dnd_class_id = serializers.IntegerField(write_only=True, required=False)
    species_id = serializers.IntegerField(write_only=True, required=False)
    background_id = serializers.IntegerField(write_only=True, required=False)
    subclass_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Character
        fields = [
            'id', 'character_name', 'level', 'level_display', 'experience_points',
            'alignment', 'dnd_class', 'dnd_class_id', 'subclass', 'subclass_id',
            'species', 'species_id', 'background', 'background_id',
            'current_hp', 'max_hp', 'temporary_hp', 'armor_class',
            'initiative', 'speed', 'proficiency_bonus', 'inspiration',
            'character_state', 'is_complete', 'additional_notes',
            'created_date', 'last_modified_date',
            'abilities', 'details', 'skills', 'saving_throws',
            'proficiencies', 'equipment', 'spells', 'feats', 'languages'
        ]
        read_only_fields = [
            'id', 'proficiency_bonus', 'created_date', 'last_modified_date'
        ]

    def update(self, instance, validated_data):
        """Update character with foreign key handling"""
        # Handle foreign key updates
        if 'dnd_class_id' in validated_data:
            instance.dnd_class_id = validated_data.pop('dnd_class_id')
        if 'species_id' in validated_data:
            instance.species_id = validated_data.pop('species_id')
        if 'background_id' in validated_data:
            instance.background_id = validated_data.pop('background_id')
        if 'subclass_id' in validated_data:
            instance.subclass_id = validated_data.pop('subclass_id')

        # Update remaining fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class CharacterAbilitiesUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating character abilities"""
    class Meta:
        model = CharacterAbilities
        fields = [
            'strength_score', 'dexterity_score', 'constitution_score',
            'intelligence_score', 'wisdom_score', 'charisma_score'
        ]

    def validate(self, data):
        """Validate ability scores are within reasonable bounds"""
        for field_name, value in data.items():
            if value < 3 or value > 20:
                raise serializers.ValidationError(
                    f"{field_name} must be between 3 and 20"
                )
        return data


class CharacterDetailsUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating character details"""
    class Meta:
        model = CharacterDetails
        fields = [
            'age', 'height', 'weight', 'eyes', 'skin', 'hair', 'pronouns',
            'portrait_url', 'personality_traits', 'ideals', 'bonds', 'flaws',
            'backstory', 'notes'
        ]