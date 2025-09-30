from django.db import models


# Skills and Abilities
ABILITY_CHOICES = [
    ('STR', 'Strength'),
    ('DEX', 'Dexterity'),
    ('CON', 'Constitution'),
    ('INT', 'Intelligence'),
    ('WIS', 'Wisdom'),
    ('CHA', 'Charisma'),
]

SIZE_CHOICES = [
    ('T', 'Tiny'),
    ('S', 'Small'),
    ('M', 'Medium'),
    ('L', 'Large'),
    ('H', 'Huge'),
    ('G', 'Gargantuan'),
]

ALIGNMENT_CHOICES = [
    ('LG', 'Lawful Good'),
    ('NG', 'Neutral Good'),
    ('CG', 'Chaotic Good'),
    ('LN', 'Lawful Neutral'),
    ('N', 'True Neutral'),
    ('CN', 'Chaotic Neutral'),
    ('LE', 'Lawful Evil'),
    ('NE', 'Neutral Evil'),
    ('CE', 'Chaotic Evil'),
]

SPELL_SCHOOL_CHOICES = [
    ('abjuration', 'Abjuration'),
    ('conjuration', 'Conjuration'),
    ('divination', 'Divination'),
    ('enchantment', 'Enchantment'),
    ('evocation', 'Evocation'),
    ('illusion', 'Illusion'),
    ('necromancy', 'Necromancy'),
    ('transmutation', 'Transmutation'),
]

DAMAGE_TYPE_CHOICES = [
    ('acid', 'Acid'),
    ('bludgeoning', 'Bludgeoning'),
    ('cold', 'Cold'),
    ('fire', 'Fire'),
    ('force', 'Force'),
    ('lightning', 'Lightning'),
    ('necrotic', 'Necrotic'),
    ('piercing', 'Piercing'),
    ('poison', 'Poison'),
    ('psychic', 'Psychic'),
    ('radiant', 'Radiant'),
    ('slashing', 'Slashing'),
    ('thunder', 'Thunder'),
]


class Skill(models.Model):
    """Core D&D Skills"""
    name = models.CharField(max_length=50, unique=True)
    associated_ability = models.CharField(max_length=3, choices=ABILITY_CHOICES)
    description = models.TextField()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Language(models.Model):
    """Languages in D&D"""
    name = models.CharField(max_length=50, unique=True)
    script = models.CharField(max_length=50, blank=True)
    typical_speakers = models.CharField(max_length=200, blank=True)
    rarity = models.CharField(
        max_length=20,
        choices=[('standard', 'Standard'), ('exotic', 'Exotic')],
        default='standard'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Feat(models.Model):
    """D&D 2024 Feats"""
    FEAT_TYPE_CHOICES = [
        ('origin', 'Origin'),
        ('general', 'General'),
        ('fighting_style', 'Fighting Style'),
    ]

    name = models.CharField(max_length=100, unique=True)
    feat_type = models.CharField(max_length=20, choices=FEAT_TYPE_CHOICES)
    description = models.TextField()
    repeatable = models.BooleanField(default=False)
    prerequisites = models.JSONField(default=dict, blank=True)
    ability_score_increase = models.JSONField(default=dict, blank=True)
    benefits = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['feat_type', 'name']

    def __str__(self):
        return self.name


class Species(models.Model):
    """D&D Species (Races)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    size = models.CharField(max_length=1, choices=SIZE_CHOICES, default='M')
    speed = models.PositiveIntegerField(default=30, help_text="Base walking speed in feet")
    darkvision_range = models.PositiveIntegerField(default=0, help_text="Darkvision range in feet (0 if none)")
    languages = models.JSONField(default=list, blank=True, help_text="List of automatic languages")

    class Meta:
        verbose_name_plural = "Species"
        ordering = ['name']

    def __str__(self):
        return self.name


class SpeciesTrait(models.Model):
    """Individual traits for Species"""
    TRAIT_TYPE_CHOICES = [
        ('racial', 'Racial Trait'),
        ('ability', 'Ability'),
        ('resistance', 'Resistance'),
        ('immunity', 'Immunity'),
        ('proficiency', 'Proficiency'),
    ]

    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name='traits')
    name = models.CharField(max_length=100)
    description = models.TextField()
    trait_type = models.CharField(max_length=20, choices=TRAIT_TYPE_CHOICES, default='racial')
    mechanical_effect = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ['species', 'name']
        ordering = ['species', 'name']

    def __str__(self):
        return f"{self.species.name} - {self.name}"


class DnDClass(models.Model):
    """D&D Classes"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('hard', 'Hard'),
    ]

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    primary_ability = models.CharField(max_length=3, choices=ABILITY_CHOICES)
    hit_die = models.PositiveIntegerField(default=8, help_text="Hit die size (d6=6, d8=8, etc.)")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='moderate')

    # JSON fields for complex data
    armor_proficiencies = models.JSONField(default=list, blank=True)
    weapon_proficiencies = models.JSONField(default=list, blank=True)
    saving_throw_proficiencies = models.JSONField(default=list, blank=True)
    skill_proficiency_count = models.PositiveIntegerField(default=2)
    skill_proficiency_choices = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        ordering = ['name']

    def __str__(self):
        return self.name


class ClassFeature(models.Model):
    """Features gained by classes at different levels"""
    FEATURE_TYPE_CHOICES = [
        ('feature', 'Class Feature'),
        ('asi', 'Ability Score Improvement'),
        ('spell', 'Spellcasting'),
        ('invocation', 'Eldritch Invocation'),
        ('maneuver', 'Fighting Maneuver'),
    ]

    dnd_class = models.ForeignKey(DnDClass, on_delete=models.CASCADE, related_name='features')
    name = models.CharField(max_length=100)
    level_acquired = models.PositiveIntegerField()
    description = models.TextField()
    feature_type = models.CharField(max_length=20, choices=FEATURE_TYPE_CHOICES, default='feature')
    uses_per_rest = models.CharField(max_length=50, blank=True, help_text="e.g., '1/long rest', 'prof bonus/long rest'")
    choice_options = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = ['dnd_class', 'name', 'level_acquired']
        ordering = ['dnd_class', 'level_acquired', 'name']

    def __str__(self):
        return f"{self.dnd_class.name} Level {self.level_acquired}: {self.name}"


class Subclass(models.Model):
    """Subclasses for each class"""
    dnd_class = models.ForeignKey(DnDClass, on_delete=models.CASCADE, related_name='subclasses')
    name = models.CharField(max_length=100)
    description = models.TextField()
    level_available = models.PositiveIntegerField(default=3)
    features = models.ManyToManyField(ClassFeature, blank=True, related_name='subclasses')

    class Meta:
        unique_together = ['dnd_class', 'name']
        ordering = ['dnd_class', 'name']

    def __str__(self):
        return f"{self.dnd_class.name} - {self.name}"


class Background(models.Model):
    """D&D Backgrounds"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    # Origin Feat (2024 rules)
    origin_feat = models.ForeignKey(
        Feat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'feat_type': 'origin'}
    )

    # JSON fields for flexible data
    skill_proficiencies = models.JSONField(default=list, blank=True)
    tool_proficiencies = models.JSONField(default=list, blank=True)
    languages = models.JSONField(default=list, blank=True)
    equipment_options = models.JSONField(default=list, blank=True)
    starting_gold = models.PositiveIntegerField(default=50)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Equipment(models.Model):
    """Base Equipment model"""
    EQUIPMENT_TYPE_CHOICES = [
        ('weapon', 'Weapon'),
        ('armor', 'Armor'),
        ('shield', 'Shield'),
        ('tool', 'Tool'),
        ('gear', 'Adventuring Gear'),
        ('instrument', 'Musical Instrument'),
        ('kit', 'Kit'),
        ('mount', 'Mount and Vehicle'),
        ('trade_good', 'Trade Good'),
    ]

    name = models.CharField(max_length=100, unique=True)
    equipment_type = models.CharField(max_length=20, choices=EQUIPMENT_TYPE_CHOICES)
    cost_gp = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Weight in pounds")
    description = models.TextField(blank=True)
    properties = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['equipment_type', 'name']

    def __str__(self):
        return self.name


class Weapon(Equipment):
    """Weapons extend Equipment"""
    WEAPON_CATEGORY_CHOICES = [
        ('simple', 'Simple'),
        ('martial', 'Martial'),
    ]

    weapon_category = models.CharField(max_length=10, choices=WEAPON_CATEGORY_CHOICES, default='simple')
    damage_dice = models.CharField(max_length=20, help_text="e.g., '1d6', '1d8', '2d6'")
    damage_type = models.CharField(max_length=20, choices=DAMAGE_TYPE_CHOICES)
    range_normal = models.PositiveIntegerField(null=True, blank=True, help_text="Normal range in feet (ranged weapons)")
    range_long = models.PositiveIntegerField(null=True, blank=True, help_text="Long range in feet (ranged weapons)")
    mastery_property = models.CharField(max_length=50, blank=True, help_text="2024 weapon mastery property")

    class Meta:
        ordering = ['weapon_category', 'name']


class Armor(Equipment):
    """Armor extends Equipment"""
    ARMOR_TYPE_CHOICES = [
        ('light', 'Light Armor'),
        ('medium', 'Medium Armor'),
        ('heavy', 'Heavy Armor'),
        ('shield', 'Shield'),
    ]

    armor_type = models.CharField(max_length=10, choices=ARMOR_TYPE_CHOICES)
    base_ac = models.PositiveIntegerField(help_text="Base AC provided")
    dex_bonus_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Max DEX bonus (null = unlimited)")
    strength_requirement = models.PositiveIntegerField(null=True, blank=True, help_text="Minimum STR required")
    stealth_disadvantage = models.BooleanField(default=False)

    class Meta:
        ordering = ['armor_type', 'name']


class Spell(models.Model):
    """D&D Spells"""
    CASTING_TIME_CHOICES = [
        ('action', 'Action'),
        ('bonus_action', 'Bonus Action'),
        ('reaction', 'Reaction'),
        ('1_minute', '1 Minute'),
        ('10_minutes', '10 Minutes'),
        ('1_hour', '1 Hour'),
        ('8_hours', '8 Hours'),
        ('24_hours', '24 Hours'),
    ]

    RANGE_CHOICES = [
        ('self', 'Self'),
        ('touch', 'Touch'),
        ('5_feet', '5 feet'),
        ('10_feet', '10 feet'),
        ('30_feet', '30 feet'),
        ('60_feet', '60 feet'),
        ('90_feet', '90 feet'),
        ('120_feet', '120 feet'),
        ('150_feet', '150 feet'),
        ('300_feet', '300 feet'),
        ('500_feet', '500 feet'),
        ('1_mile', '1 mile'),
        ('sight', 'Sight'),
        ('unlimited', 'Unlimited'),
        ('special', 'Special'),
    ]

    DURATION_CHOICES = [
        ('instantaneous', 'Instantaneous'),
        ('1_round', '1 round'),
        ('1_minute', '1 minute'),
        ('10_minutes', '10 minutes'),
        ('1_hour', '1 hour'),
        ('8_hours', '8 hours'),
        ('24_hours', '24 hours'),
        ('7_days', '7 days'),
        ('30_days', '30 days'),
        ('permanent', 'Until dispelled'),
        ('special', 'Special'),
    ]

    name = models.CharField(max_length=100, unique=True)
    spell_level = models.PositiveIntegerField(help_text="0 for cantrips, 1-9 for spell levels")
    school = models.CharField(max_length=20, choices=SPELL_SCHOOL_CHOICES)
    casting_time = models.CharField(max_length=20, choices=CASTING_TIME_CHOICES)
    range = models.CharField(max_length=20, choices=RANGE_CHOICES)
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES)
    concentration = models.BooleanField(default=False)
    ritual = models.BooleanField(default=False)

    # Components
    components_v = models.BooleanField(default=False, help_text="Verbal component")
    components_s = models.BooleanField(default=False, help_text="Somatic component")
    components_m = models.BooleanField(default=False, help_text="Material component")
    material_components = models.CharField(max_length=500, blank=True)

    # Descriptions
    description = models.TextField()
    higher_level_description = models.TextField(blank=True, help_text="At Higher Levels effect")

    # Available to which classes
    available_to_classes = models.ManyToManyField(DnDClass, blank=True, related_name='spells')

    class Meta:
        ordering = ['spell_level', 'name']

    def __str__(self):
        level_text = "Cantrip" if self.spell_level == 0 else f"Level {self.spell_level}"
        return f"{self.name} ({level_text})"

    @property
    def components_display(self):
        """Return a formatted string of spell components"""
        components = []
        if self.components_v:
            components.append('V')
        if self.components_s:
            components.append('S')
        if self.components_m:
            if self.material_components:
                components.append(f'M ({self.material_components})')
            else:
                components.append('M')
        return ', '.join(components)
