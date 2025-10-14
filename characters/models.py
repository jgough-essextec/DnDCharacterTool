from django.db import models
from django.contrib.auth import get_user_model
from game_content.models import (
    DnDClass, Subclass, Background, Species, Feat, Skill,
    Equipment, Spell, Language, ALIGNMENT_CHOICES, ABILITY_CHOICES
)

User = get_user_model()


class Character(models.Model):
    """Main Character model"""
    CHARACTER_STATE_CHOICES = [
        ('draft', 'Draft'),
        ('complete', 'Complete'),
        ('archived', 'Archived'),
    ]

    # Basic Info
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='characters')
    character_name = models.CharField(max_length=100)
    level = models.PositiveIntegerField(default=1)
    experience_points = models.PositiveIntegerField(default=0)
    alignment = models.CharField(max_length=2, choices=ALIGNMENT_CHOICES, blank=True)

    # Class/Background/Species
    dnd_class = models.ForeignKey(DnDClass, on_delete=models.PROTECT, null=True, blank=True)
    subclass = models.ForeignKey(Subclass, on_delete=models.SET_NULL, null=True, blank=True)
    background = models.ForeignKey(Background, on_delete=models.PROTECT, null=True, blank=True)
    species = models.ForeignKey(Species, on_delete=models.PROTECT, null=True, blank=True)

    # Combat Stats
    current_hp = models.PositiveIntegerField(default=0)
    max_hp = models.PositiveIntegerField(default=0)
    temporary_hp = models.PositiveIntegerField(default=0)
    armor_class = models.PositiveIntegerField(default=10)
    initiative = models.IntegerField(default=0)
    speed = models.PositiveIntegerField(default=30)
    proficiency_bonus = models.PositiveIntegerField(default=2)
    inspiration = models.BooleanField(default=False)

    # Meta
    additional_notes = models.JSONField(default=dict, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    last_modified_date = models.DateTimeField(auto_now=True)
    is_complete = models.BooleanField(default=False)
    character_state = models.CharField(max_length=10, choices=CHARACTER_STATE_CHOICES, default='draft')

    class Meta:
        unique_together = ['user', 'character_name']
        ordering = ['-last_modified_date']

    def __str__(self):
        return f"{self.character_name} ({self.user.username})"

    @property
    def level_display(self):
        """Return formatted level with class info"""
        if self.dnd_class:
            return f"Level {self.level} {self.dnd_class.name}"
        return f"Level {self.level}"

    def calculate_proficiency_bonus(self):
        """Calculate proficiency bonus based on level"""
        return 2 + ((self.level - 1) // 4)

    def save(self, *args, **kwargs):
        """Auto-calculate proficiency bonus on save"""
        self.proficiency_bonus = self.calculate_proficiency_bonus()
        super().save(*args, **kwargs)

    def get_calculation_service(self):
        """Get calculation service instance for this character"""
        from .services import CharacterCalculationService
        return CharacterCalculationService(self)

    def get_validation_service(self):
        """Get validation service instance for this character"""
        from .services import CharacterValidationService
        return CharacterValidationService(self)

    def calculate_max_hp(self):
        """Calculate maximum HP using calculation service"""
        return self.get_calculation_service().calculate_max_hp()

    def calculate_ac(self):
        """Calculate armor class using calculation service"""
        return self.get_calculation_service().calculate_armor_class()

    def get_all_stats(self):
        """Get complete calculated statistics"""
        return self.get_calculation_service().get_complete_character_stats()

    def validate_build(self):
        """Validate character build for rule compliance"""
        return self.get_validation_service().validate_character()

    def auto_calculate_stats(self):
        """Auto-calculate and update derived stats"""
        calc_service = self.get_calculation_service()

        # Update calculated values
        self.max_hp = calc_service.calculate_max_hp()
        self.armor_class = calc_service.calculate_armor_class()
        self.initiative = calc_service.calculate_initiative()

        # Save without triggering recursion
        super().save(update_fields=['max_hp', 'armor_class', 'initiative'])


class CharacterAbilities(models.Model):
    """Character's six ability scores"""
    character = models.OneToOneField(Character, on_delete=models.CASCADE, related_name='abilities')

    strength_score = models.PositiveIntegerField(default=10)
    dexterity_score = models.PositiveIntegerField(default=10)
    constitution_score = models.PositiveIntegerField(default=10)
    intelligence_score = models.PositiveIntegerField(default=10)
    wisdom_score = models.PositiveIntegerField(default=10)
    charisma_score = models.PositiveIntegerField(default=10)

    class Meta:
        verbose_name_plural = "Character Abilities"

    def __str__(self):
        return f"{self.character.character_name} - Abilities"

    @staticmethod
    def modifier(score):
        """Calculate ability modifier from score"""
        return (score - 10) // 2

    @property
    def strength_modifier(self):
        return self.modifier(self.strength_score)

    @property
    def dexterity_modifier(self):
        return self.modifier(self.dexterity_score)

    @property
    def constitution_modifier(self):
        return self.modifier(self.constitution_score)

    @property
    def intelligence_modifier(self):
        return self.modifier(self.intelligence_score)

    @property
    def wisdom_modifier(self):
        return self.modifier(self.wisdom_score)

    @property
    def charisma_modifier(self):
        return self.modifier(self.charisma_score)

    def get_modifier_for_ability(self, ability_name):
        """Get modifier for ability by name (STR, DEX, etc.)"""
        ability_map = {
            'STR': self.strength_modifier,
            'DEX': self.dexterity_modifier,
            'CON': self.constitution_modifier,
            'INT': self.intelligence_modifier,
            'WIS': self.wisdom_modifier,
            'CHA': self.charisma_modifier,
        }
        return ability_map.get(ability_name, 0)


class CharacterSkill(models.Model):
    """Character skill proficiencies"""
    PROFICIENCY_TYPE_CHOICES = [
        ('none', 'Not Proficient'),
        ('proficient', 'Proficient'),
        ('expertise', 'Expertise'),
    ]

    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency_type = models.CharField(max_length=12, choices=PROFICIENCY_TYPE_CHOICES, default='none')

    class Meta:
        unique_together = ['character', 'skill']

    def __str__(self):
        return f"{self.character.character_name} - {self.skill.name} ({self.proficiency_type})"

    @property
    def bonus(self):
        """Calculate total skill bonus"""
        if not self.character.abilities:
            return 0

        ability_mod = self.character.abilities.get_modifier_for_ability(self.skill.associated_ability)
        prof_bonus = self.character.proficiency_bonus if self.proficiency_type != 'none' else 0

        # Expertise doubles proficiency bonus
        if self.proficiency_type == 'expertise':
            prof_bonus *= 2

        return ability_mod + prof_bonus


class CharacterSavingThrow(models.Model):
    """Character saving throw proficiencies"""
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='saving_throws')
    ability_name = models.CharField(max_length=3, choices=ABILITY_CHOICES)
    is_proficient = models.BooleanField(default=False)

    class Meta:
        unique_together = ['character', 'ability_name']

    def __str__(self):
        return f"{self.character.character_name} - {self.ability_name} Save"

    @property
    def bonus(self):
        """Calculate saving throw bonus"""
        if not self.character.abilities:
            return 0

        ability_mod = self.character.abilities.get_modifier_for_ability(self.ability_name)
        prof_bonus = self.character.proficiency_bonus if self.is_proficient else 0
        return ability_mod + prof_bonus


class CharacterProficiency(models.Model):
    """Generic proficiencies (armor, weapons, tools)"""
    PROFICIENCY_TYPE_CHOICES = [
        ('armor', 'Armor'),
        ('weapon', 'Weapon'),
        ('tool', 'Tool'),
        ('language', 'Language'),
    ]

    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='proficiencies')
    proficiency_type = models.CharField(max_length=10, choices=PROFICIENCY_TYPE_CHOICES)
    proficiency_name = models.CharField(max_length=100)

    class Meta:
        unique_together = ['character', 'proficiency_type', 'proficiency_name']

    def __str__(self):
        return f"{self.character.character_name} - {self.proficiency_name} ({self.proficiency_type})"


class CharacterEquipment(models.Model):
    """Character's equipment inventory"""
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='equipment')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    equipped = models.BooleanField(default=False)
    attuned = models.BooleanField(default=False, help_text="For magic items requiring attunement")

    class Meta:
        unique_together = ['character', 'equipment']

    def __str__(self):
        equipped_text = " (Equipped)" if self.equipped else ""
        return f"{self.character.character_name} - {self.equipment.name} x{self.quantity}{equipped_text}"


class CharacterSpell(models.Model):
    """Character's known/prepared spells"""
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='spells')
    spell = models.ForeignKey(Spell, on_delete=models.CASCADE)
    always_prepared = models.BooleanField(default=False, help_text="Always prepared (racial, class features, etc.)")
    prepared = models.BooleanField(default=False, help_text="Currently prepared")

    class Meta:
        unique_together = ['character', 'spell']

    def __str__(self):
        prepared_text = " (Prepared)" if self.prepared or self.always_prepared else ""
        return f"{self.character.character_name} - {self.spell.name}{prepared_text}"


class CharacterFeature(models.Model):
    """Character's class features and their usage"""
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='class_features')
    class_feature = models.ForeignKey('game_content.ClassFeature', on_delete=models.CASCADE)
    uses_remaining = models.PositiveIntegerField(default=0, help_text="Uses remaining (if limited)")
    choice_made = models.JSONField(default=dict, blank=True, help_text="Choices made for this feature")

    class Meta:
        unique_together = ['character', 'class_feature']

    def __str__(self):
        return f"{self.character.character_name} - {self.class_feature.name}"


class CharacterFeat(models.Model):
    """Character's feats"""
    FEAT_SOURCE_CHOICES = [
        ('background', 'Background'),
        ('class', 'Class Feature'),
        ('asi', 'Ability Score Improvement'),
        ('species', 'Species'),
    ]

    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='feats')
    feat = models.ForeignKey(Feat, on_delete=models.CASCADE)
    source = models.CharField(max_length=12, choices=FEAT_SOURCE_CHOICES)
    choice_made = models.JSONField(default=dict, blank=True, help_text="Choices made for this feat")

    class Meta:
        unique_together = ['character', 'feat', 'source']

    def __str__(self):
        return f"{self.character.character_name} - {self.feat.name} ({self.source})"


class CharacterLanguage(models.Model):
    """Character's known languages"""
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='languages')
    language = models.ForeignKey(Language, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['character', 'language']

    def __str__(self):
        return f"{self.character.character_name} - {self.language.name}"


class CharacterDetails(models.Model):
    """Character's appearance and personality details"""
    character = models.OneToOneField(Character, on_delete=models.CASCADE, related_name='details')

    # Physical Description
    age = models.PositiveIntegerField(null=True, blank=True)
    height = models.CharField(max_length=20, blank=True)
    weight = models.CharField(max_length=20, blank=True)
    eyes = models.CharField(max_length=50, blank=True)
    skin = models.CharField(max_length=50, blank=True)
    hair = models.CharField(max_length=50, blank=True)
    pronouns = models.CharField(max_length=50, blank=True)

    # Portrait
    portrait_url = models.URLField(blank=True, help_text="S3 URL for character portrait")

    # Personality
    personality_traits = models.TextField(blank=True, help_text="Character's personality traits")
    ideals = models.TextField(blank=True, help_text="Character's ideals and motivations")
    bonds = models.TextField(blank=True, help_text="Character's bonds and connections")
    flaws = models.TextField(blank=True, help_text="Character's flaws and weaknesses")
    backstory = models.TextField(blank=True, help_text="Character's backstory")
    notes = models.TextField(blank=True, help_text="Additional character notes")

    class Meta:
        verbose_name_plural = "Character Details"

    def __str__(self):
        return f"{self.character.character_name} - Details"
