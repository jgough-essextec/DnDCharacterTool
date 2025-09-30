from django.contrib import admin
from .models import (
    Character, CharacterAbilities, CharacterSkill, CharacterSavingThrow,
    CharacterProficiency, CharacterEquipment, CharacterSpell,
    CharacterFeature, CharacterFeat, CharacterLanguage, CharacterDetails
)


class CharacterAbilitiesInline(admin.StackedInline):
    model = CharacterAbilities
    can_delete = False
    verbose_name_plural = 'Ability Scores'
    fields = (
        ('strength_score', 'dexterity_score', 'constitution_score'),
        ('intelligence_score', 'wisdom_score', 'charisma_score')
    )


class CharacterDetailsInline(admin.StackedInline):
    model = CharacterDetails
    can_delete = False
    verbose_name_plural = 'Character Details'
    fieldsets = (
        ('Physical Description', {
            'fields': ('age', 'height', 'weight', 'eyes', 'skin', 'hair', 'pronouns', 'portrait_url')
        }),
        ('Personality', {
            'fields': ('personality_traits', 'ideals', 'bonds', 'flaws'),
            'classes': ('collapse',)
        }),
        ('Background', {
            'fields': ('backstory', 'notes'),
            'classes': ('collapse',)
        }),
    )


class CharacterSkillInline(admin.TabularInline):
    model = CharacterSkill
    extra = 0
    fields = ('skill', 'proficiency_type')
    ordering = ('skill__name',)


class CharacterSavingThrowInline(admin.TabularInline):
    model = CharacterSavingThrow
    extra = 0
    fields = ('ability_name', 'is_proficient')
    ordering = ('ability_name',)


class CharacterEquipmentInline(admin.TabularInline):
    model = CharacterEquipment
    extra = 0
    fields = ('equipment', 'quantity', 'equipped', 'attuned')
    ordering = ('equipment__name',)


class CharacterSpellInline(admin.TabularInline):
    model = CharacterSpell
    extra = 0
    fields = ('spell', 'always_prepared', 'prepared')
    ordering = ('spell__spell_level', 'spell__name')


class CharacterFeatInline(admin.TabularInline):
    model = CharacterFeat
    extra = 0
    fields = ('feat', 'source', 'choice_made')
    ordering = ('feat__name',)


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('character_name', 'user', 'level_display', 'species', 'dnd_class', 'character_state', 'last_modified_date')
    list_filter = ('character_state', 'dnd_class', 'species', 'level', 'is_complete')
    search_fields = ('character_name', 'user__username', 'user__email')
    ordering = ('-last_modified_date',)
    readonly_fields = ('created_date', 'last_modified_date', 'proficiency_bonus')

    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'character_name', 'character_state', 'is_complete')
        }),
        ('Character Build', {
            'fields': ('dnd_class', 'subclass', 'background', 'species', 'alignment')
        }),
        ('Progression', {
            'fields': ('level', 'experience_points', 'proficiency_bonus')
        }),
        ('Combat Stats', {
            'fields': ('current_hp', 'max_hp', 'temporary_hp', 'armor_class', 'initiative', 'speed', 'inspiration')
        }),
        ('Meta', {
            'fields': ('additional_notes', 'created_date', 'last_modified_date'),
            'classes': ('collapse',)
        }),
    )

    inlines = [
        CharacterAbilitiesInline,
        CharacterDetailsInline,
        CharacterSkillInline,
        CharacterSavingThrowInline,
        CharacterEquipmentInline,
        CharacterSpellInline,
        CharacterFeatInline,
    ]

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'user', 'dnd_class', 'subclass', 'background', 'species'
        ).prefetch_related(
            'skills', 'equipment', 'spells', 'feats'
        )

    def save_related(self, request, form, formsets, change):
        """Auto-create CharacterAbilities and CharacterDetails if they don't exist"""
        super().save_related(request, form, formsets, change)
        character = form.instance

        # Create CharacterAbilities if it doesn't exist
        if not hasattr(character, 'abilities'):
            CharacterAbilities.objects.create(character=character)

        # Create CharacterDetails if it doesn't exist
        if not hasattr(character, 'details'):
            CharacterDetails.objects.create(character=character)


@admin.register(CharacterAbilities)
class CharacterAbilitiesAdmin(admin.ModelAdmin):
    list_display = ('character', 'strength_score', 'dexterity_score', 'constitution_score', 'intelligence_score', 'wisdom_score', 'charisma_score')
    search_fields = ('character__character_name', 'character__user__username')
    ordering = ('character__character_name',)


@admin.register(CharacterSkill)
class CharacterSkillAdmin(admin.ModelAdmin):
    list_display = ('character', 'skill', 'proficiency_type', 'bonus')
    list_filter = ('proficiency_type', 'skill')
    search_fields = ('character__character_name', 'skill__name')
    ordering = ('character__character_name', 'skill__name')

    def bonus(self, obj):
        """Display calculated skill bonus"""
        return f"+{obj.bonus}" if obj.bonus >= 0 else str(obj.bonus)
    bonus.short_description = 'Bonus'


@admin.register(CharacterEquipment)
class CharacterEquipmentAdmin(admin.ModelAdmin):
    list_display = ('character', 'equipment', 'quantity', 'equipped', 'attuned')
    list_filter = ('equipped', 'attuned', 'equipment__equipment_type')
    search_fields = ('character__character_name', 'equipment__name')
    ordering = ('character__character_name', 'equipment__name')


@admin.register(CharacterSpell)
class CharacterSpellAdmin(admin.ModelAdmin):
    list_display = ('character', 'spell', 'prepared', 'always_prepared')
    list_filter = ('prepared', 'always_prepared', 'spell__spell_level', 'spell__school')
    search_fields = ('character__character_name', 'spell__name')
    ordering = ('character__character_name', 'spell__spell_level', 'spell__name')


@admin.register(CharacterFeat)
class CharacterFeatAdmin(admin.ModelAdmin):
    list_display = ('character', 'feat', 'source')
    list_filter = ('source', 'feat__feat_type')
    search_fields = ('character__character_name', 'feat__name')
    ordering = ('character__character_name', 'feat__name')


# Register remaining models with simple admin
admin.site.register(CharacterSavingThrow)
admin.site.register(CharacterProficiency)
admin.site.register(CharacterFeature)
admin.site.register(CharacterLanguage)
admin.site.register(CharacterDetails)
