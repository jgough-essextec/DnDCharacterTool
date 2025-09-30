from django.contrib import admin
from .models import (
    Skill, Language, Feat, Species, SpeciesTrait,
    DnDClass, ClassFeature, Subclass, Background,
    Equipment, Weapon, Armor, Spell
)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'associated_ability', 'description')
    list_filter = ('associated_ability',)
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'script', 'rarity', 'typical_speakers')
    list_filter = ('rarity',)
    search_fields = ('name', 'typical_speakers')
    ordering = ('name',)


@admin.register(Feat)
class FeatAdmin(admin.ModelAdmin):
    list_display = ('name', 'feat_type', 'repeatable')
    list_filter = ('feat_type', 'repeatable')
    search_fields = ('name', 'description')
    ordering = ('feat_type', 'name')


class SpeciesTraitInline(admin.TabularInline):
    model = SpeciesTrait
    extra = 0
    fields = ('name', 'trait_type', 'description')


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ('name', 'size', 'speed', 'darkvision_range')
    list_filter = ('size',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    inlines = [SpeciesTraitInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description')
        }),
        ('Physical Traits', {
            'fields': ('size', 'speed', 'darkvision_range')
        }),
        ('Languages', {
            'fields': ('languages',)
        }),
    )


class ClassFeatureInline(admin.TabularInline):
    model = ClassFeature
    extra = 0
    fields = ('name', 'level_acquired', 'feature_type', 'uses_per_rest')
    ordering = ('level_acquired', 'name')


@admin.register(DnDClass)
class DnDClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'primary_ability', 'hit_die', 'difficulty', 'skill_proficiency_count')
    list_filter = ('primary_ability', 'difficulty', 'hit_die')
    search_fields = ('name', 'description')
    ordering = ('name',)
    inlines = [ClassFeatureInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'difficulty')
        }),
        ('Mechanics', {
            'fields': ('primary_ability', 'hit_die')
        }),
        ('Proficiencies', {
            'fields': ('armor_proficiencies', 'weapon_proficiencies', 'saving_throw_proficiencies')
        }),
        ('Skills', {
            'fields': ('skill_proficiency_count', 'skill_proficiency_choices')
        }),
    )


@admin.register(ClassFeature)
class ClassFeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'dnd_class', 'level_acquired', 'feature_type')
    list_filter = ('dnd_class', 'level_acquired', 'feature_type')
    search_fields = ('name', 'description')
    ordering = ('dnd_class', 'level_acquired', 'name')


@admin.register(Subclass)
class SubclassAdmin(admin.ModelAdmin):
    list_display = ('name', 'dnd_class', 'level_available')
    list_filter = ('dnd_class', 'level_available')
    search_fields = ('name', 'description')
    ordering = ('dnd_class', 'name')
    filter_horizontal = ('features',)


@admin.register(Background)
class BackgroundAdmin(admin.ModelAdmin):
    list_display = ('name', 'origin_feat', 'starting_gold')
    list_filter = ('origin_feat',)
    search_fields = ('name', 'description')
    ordering = ('name',)

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description')
        }),
        ('2024 Rules', {
            'fields': ('origin_feat',)
        }),
        ('Proficiencies', {
            'fields': ('skill_proficiencies', 'tool_proficiencies', 'languages')
        }),
        ('Equipment', {
            'fields': ('equipment_options', 'starting_gold')
        }),
    )


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'equipment_type', 'cost_gp', 'weight')
    list_filter = ('equipment_type',)
    search_fields = ('name', 'description')
    ordering = ('equipment_type', 'name')


@admin.register(Weapon)
class WeaponAdmin(admin.ModelAdmin):
    list_display = ('name', 'weapon_category', 'damage_dice', 'damage_type', 'cost_gp')
    list_filter = ('weapon_category', 'damage_type')
    search_fields = ('name', 'description')
    ordering = ('weapon_category', 'name')

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'equipment_type')
        }),
        ('Combat Stats', {
            'fields': ('weapon_category', 'damage_dice', 'damage_type', 'mastery_property')
        }),
        ('Range', {
            'fields': ('range_normal', 'range_long')
        }),
        ('Economics', {
            'fields': ('cost_gp', 'weight')
        }),
        ('Properties', {
            'fields': ('properties',)
        }),
    )


@admin.register(Armor)
class ArmorAdmin(admin.ModelAdmin):
    list_display = ('name', 'armor_type', 'base_ac', 'dex_bonus_limit', 'stealth_disadvantage', 'cost_gp')
    list_filter = ('armor_type', 'stealth_disadvantage')
    search_fields = ('name', 'description')
    ordering = ('armor_type', 'name')

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'equipment_type')
        }),
        ('Armor Stats', {
            'fields': ('armor_type', 'base_ac', 'dex_bonus_limit', 'strength_requirement', 'stealth_disadvantage')
        }),
        ('Economics', {
            'fields': ('cost_gp', 'weight')
        }),
        ('Properties', {
            'fields': ('properties',)
        }),
    )


@admin.register(Spell)
class SpellAdmin(admin.ModelAdmin):
    list_display = ('name', 'spell_level', 'school', 'casting_time', 'concentration', 'ritual')
    list_filter = ('spell_level', 'school', 'concentration', 'ritual', 'available_to_classes')
    search_fields = ('name', 'description')
    ordering = ('spell_level', 'name')
    filter_horizontal = ('available_to_classes',)

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'spell_level', 'school')
        }),
        ('Casting', {
            'fields': ('casting_time', 'range', 'duration', 'concentration', 'ritual')
        }),
        ('Components', {
            'fields': ('components_v', 'components_s', 'components_m', 'material_components')
        }),
        ('Description', {
            'fields': ('description', 'higher_level_description')
        }),
        ('Availability', {
            'fields': ('available_to_classes',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with prefetch_related"""
        return super().get_queryset(request).prefetch_related('available_to_classes')
