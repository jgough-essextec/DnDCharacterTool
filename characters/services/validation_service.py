"""
Character Validation Service

Handles all character validation including:
- D&D rule compliance
- Ability score validation
- Equipment requirements
- Spell slot limits
- Class feature prerequisites
- Character build integrity
"""
from typing import Dict, List, Optional, Tuple
from django.core.exceptions import ValidationError
from django.db.models import Q

from ..models import Character, CharacterAbilities, CharacterEquipment, CharacterSpell
from game_content.models import Skill, Spell


class CharacterValidationService:
    """Service class for validating character data against D&D rules"""

    @staticmethod
    def validate_ability_scores(scores: Dict[str, int], method: str = 'standard_array') -> Dict[str, List[str]]:
        """
        Validate ability scores based on generation method

        Args:
            scores: Dict with ability names and scores
            method: 'standard_array', 'point_buy', or 'roll'

        Returns:
            Dict with validation errors by field
        """
        errors = {}

        # Check score ranges (3-20 for most cases, 8-15 for point buy base)
        for ability, score in scores.items():
            ability_errors = []

            if method == 'point_buy':
                if score < 8 or score > 15:
                    ability_errors.append(f"{ability} must be between 8-15 for point buy")
            else:
                if score < 3 or score > 20:
                    ability_errors.append(f"{ability} must be between 3-20")

            if ability_errors:
                errors[ability] = ability_errors

        # Validate point buy total cost
        if method == 'point_buy':
            point_buy_errors = CharacterValidationService._validate_point_buy_cost(scores)
            if point_buy_errors:
                errors['point_buy'] = point_buy_errors

        # Validate standard array usage
        if method == 'standard_array':
            array_errors = CharacterValidationService._validate_standard_array(scores)
            if array_errors:
                errors['standard_array'] = array_errors

        return errors

    @staticmethod
    def _validate_point_buy_cost(scores: Dict[str, int]) -> List[str]:
        """Validate point buy doesn't exceed 27 points"""
        # Point buy costs: 8=0, 9=1, 10=2, 11=3, 12=4, 13=5, 14=7, 15=9
        cost_table = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}

        total_cost = 0
        for score in scores.values():
            if score in cost_table:
                total_cost += cost_table[score]
            else:
                return [f"Invalid score {score} for point buy"]

        if total_cost > 27:
            return [f"Point buy total ({total_cost}) exceeds maximum of 27 points"]

        return []

    @staticmethod
    def _validate_standard_array(scores: Dict[str, int]) -> List[str]:
        """Validate standard array uses exactly [15, 14, 13, 12, 10, 8]"""
        standard_scores = [15, 14, 13, 12, 10, 8]
        used_scores = sorted(scores.values(), reverse=True)

        if used_scores != standard_scores:
            return [f"Standard array must use exactly {standard_scores}, got {used_scores}"]

        return []

    @classmethod
    def validate_character_skills(cls, character: Character) -> Dict[str, List[str]]:
        """
        Validate character skill selections

        Checks:
        - Correct number of skills for class/background
        - No duplicate selections
        - Valid skill choices
        """
        errors = {}

        if not character.dnd_class:
            return {'class': ['Character must have a class selected']}

        # Get expected skill count from class
        class_skill_count = character.dnd_class.skill_choices
        background_skill_count = 2 if character.background else 0

        # Count current skills by source
        class_skills = character.skills.filter(source='class').count()
        background_skills = character.skills.filter(source='background').count()

        # Validate class skill count
        if class_skills != class_skill_count:
            errors['class_skills'] = [
                f"Class requires {class_skill_count} skills, but {class_skills} selected"
            ]

        # Validate background skill count
        if background_skills != background_skill_count:
            errors['background_skills'] = [
                f"Background requires {background_skill_count} skills, but {background_skills} selected"
            ]

        # Check for duplicate skills
        skill_names = list(character.skills.values_list('skill__name', flat=True))
        if len(skill_names) != len(set(skill_names)):
            errors['duplicates'] = ['Cannot select the same skill multiple times']

        # Validate skill choices are valid for class/background
        if character.dnd_class.skill_options:
            valid_class_skills = character.dnd_class.skill_options
            invalid_class_skills = character.skills.filter(
                source='class'
            ).exclude(skill__name__in=valid_class_skills).values_list('skill__name', flat=True)

            if invalid_class_skills:
                errors['invalid_class_skills'] = [
                    f"Invalid class skills: {list(invalid_class_skills)}"
                ]

        return errors

    @classmethod
    def validate_character_equipment(cls, character: Character) -> Dict[str, List[str]]:
        """
        Validate character equipment selections

        Checks:
        - Armor proficiency
        - Weapon proficiency
        - Shield requirements
        - Encumbrance limits
        - Equipment conflicts
        """
        errors = {}

        if not character.dnd_class:
            return errors

        # Get equipped items
        equipped_armor = character.equipment.filter(
            equipped=True,
            equipment__armor__isnull=False
        ).select_related('equipment__armor')

        equipped_weapons = character.equipment.filter(
            equipped=True,
            equipment__weapon__isnull=False
        ).select_related('equipment__weapon')

        # Validate armor proficiency
        for char_equipment in equipped_armor:
            armor = char_equipment.equipment.armor
            class_armor_profs = character.dnd_class.armor_proficiencies or []

            if armor.armor_type not in class_armor_profs and 'all' not in class_armor_profs:
                errors.setdefault('armor_proficiency', []).append(
                    f"Not proficient with {armor.armor_type} armor: {armor.name}"
                )

        # Validate weapon proficiency
        for char_equipment in equipped_weapons:
            weapon = char_equipment.equipment.weapon
            class_weapon_profs = character.dnd_class.weapon_proficiencies or []

            is_proficient = (
                weapon.weapon_category in class_weapon_profs or
                'all' in class_weapon_profs or
                weapon.name.lower() in [prof.lower() for prof in class_weapon_profs]
            )

            if not is_proficient:
                errors.setdefault('weapon_proficiency', []).append(
                    f"Not proficient with weapon: {weapon.name}"
                )

        # Check multiple armor pieces
        if equipped_armor.count() > 1:
            errors['multiple_armor'] = ['Cannot wear multiple pieces of armor']

        # Check shield + two-handed weapon conflict
        has_shield = character.equipment.filter(
            equipped=True,
            equipment__name__icontains='shield'
        ).exists()

        two_handed_weapons = equipped_weapons.filter(
            equipment__weapon__properties__contains=['two-handed']
        )

        if has_shield and two_handed_weapons.exists():
            errors['shield_conflict'] = ['Cannot use shield with two-handed weapon']

        # Validate encumbrance
        from .calculation_service import CharacterCalculationService
        encumbrance_status = CharacterCalculationService.get_encumbrance_status(character)

        if encumbrance_status == 'overloaded':
            errors['encumbrance'] = ['Character is overloaded (exceeds carrying capacity)']

        return errors

    @classmethod
    def validate_character_spells(cls, character: Character) -> Dict[str, List[str]]:
        """
        Validate character spell selections

        Checks:
        - Spell availability for class
        - Correct number of cantrips/spells known
        - Spell level requirements
        - Prepared spell limits
        """
        errors = {}

        if not character.dnd_class or not character.dnd_class.spellcaster:
            return errors

        # Get spell progression for class and level
        spell_progression = character.dnd_class.get_spell_progression(character.level)

        if not spell_progression:
            return errors

        # Count current spells by level
        cantrips = character.spells.filter(spell__spell_level=0)
        first_level_spells = character.spells.filter(spell__spell_level=1)

        # Validate cantrip count
        expected_cantrips = spell_progression.get('cantrips_known', 0)
        actual_cantrips = cantrips.count()

        if actual_cantrips != expected_cantrips:
            errors['cantrips'] = [
                f"Should know {expected_cantrips} cantrips, but has {actual_cantrips}"
            ]

        # Validate 1st level spells known (for classes that learn spells)
        if 'spells_known' in spell_progression:
            expected_spells = spell_progression['spells_known']
            actual_spells = first_level_spells.count()

            if actual_spells != expected_spells:
                errors['spells_known'] = [
                    f"Should know {expected_spells} 1st-level spells, but has {actual_spells}"
                ]

        # Validate spell availability for class
        class_spell_list = Spell.objects.filter(available_to_classes=character.dnd_class)
        invalid_spells = character.spells.exclude(
            spell__in=class_spell_list
        ).values_list('spell__name', flat=True)

        if invalid_spells:
            errors['invalid_spells'] = [
                f"Spells not available to {character.dnd_class.name}: {list(invalid_spells)}"
            ]

        # Validate prepared spells (for prepared casters)
        if character.dnd_class.spell_preparation == 'prepared':
            max_prepared = cls._calculate_max_prepared_spells(character)
            prepared_count = character.spells.filter(prepared=True).count()

            if prepared_count > max_prepared:
                errors['prepared_spells'] = [
                    f"Too many prepared spells: {prepared_count}/{max_prepared}"
                ]

        return errors

    @staticmethod
    def _calculate_max_prepared_spells(character: Character) -> int:
        """Calculate maximum prepared spells for prepared casters"""
        if not hasattr(character, 'abilities'):
            return 0

        spellcasting_ability = character.dnd_class.primary_ability
        ability_modifier = (
            getattr(character.abilities, f"{spellcasting_ability.lower()}_score") - 10
        ) // 2

        return max(1, character.level + ability_modifier)

    @classmethod
    def validate_character_feats(cls, character: Character) -> Dict[str, List[str]]:
        """
        Validate character feat selections

        Checks:
        - Feat prerequisites
        - Ability Score Improvement usage
        - Origin feat requirements
        """
        errors = {}

        # Validate origin feat (from background)
        if character.background and character.background.origin_feat:
            has_origin_feat = character.feats.filter(
                feat=character.background.origin_feat,
                source='background'
            ).exists()

            if not has_origin_feat:
                errors['origin_feat'] = [
                    f"Must select origin feat: {character.background.origin_feat.name}"
                ]

        # Validate feat prerequisites
        for character_feat in character.feats.all():
            feat = character_feat.feat

            if feat.prerequisites:
                prereq_errors = cls._validate_feat_prerequisites(character, feat.prerequisites)
                if prereq_errors:
                    errors.setdefault('feat_prerequisites', []).extend(prereq_errors)

        # Validate ASI/Feat choices at appropriate levels
        asi_levels = cls._get_asi_levels_for_class(character.dnd_class)
        available_asi = sum(1 for level in asi_levels if level <= character.level)

        # Count non-origin feats (ASI choices)
        asi_feats = character.feats.exclude(source='background').count()

        # This is a soft validation - character might have used ASI for ability scores instead
        if asi_feats > available_asi:
            errors['too_many_feats'] = [
                f"More feats than ASI opportunities: {asi_feats}/{available_asi}"
            ]

        return errors

    @staticmethod
    def _validate_feat_prerequisites(character: Character, prerequisites: Dict) -> List[str]:
        """Validate feat prerequisites are met"""
        errors = []

        if not hasattr(character, 'abilities'):
            return ["Character abilities not set"]

        # Check ability score prerequisites
        if 'abilities' in prerequisites:
            for ability, min_score in prerequisites['abilities'].items():
                actual_score = getattr(character.abilities, f"{ability.lower()}_score")
                if actual_score < min_score:
                    errors.append(
                        f"Requires {ability.upper()} {min_score}, but has {actual_score}"
                    )

        # Check level prerequisites
        if 'level' in prerequisites:
            if character.level < prerequisites['level']:
                errors.append(
                    f"Requires level {prerequisites['level']}, but character is level {character.level}"
                )

        # Check class prerequisites
        if 'classes' in prerequisites:
            if character.dnd_class.name not in prerequisites['classes']:
                errors.append(
                    f"Requires one of: {prerequisites['classes']}"
                )

        return errors

    @staticmethod
    def _get_asi_levels_for_class(dnd_class) -> List[int]:
        """Get levels where class gets Ability Score Improvements"""
        if not dnd_class:
            return []

        # Standard ASI levels for most classes
        standard_asi = [4, 8, 12, 16, 19]

        # Fighter gets extra ASIs
        if dnd_class.name == 'Fighter':
            return [4, 6, 8, 12, 14, 16, 19]

        # Rogue gets extra ASI
        if dnd_class.name == 'Rogue':
            return [4, 8, 10, 12, 16, 19]

        return standard_asi

    @classmethod
    def validate_complete_character(cls, character: Character) -> Dict[str, List[str]]:
        """
        Comprehensive validation for a complete character

        Returns all validation errors organized by category
        """
        all_errors = {}

        # Basic character validation
        if not character.character_name or character.character_name.strip() == '':
            all_errors['name'] = ['Character name is required']

        if not character.dnd_class:
            all_errors['class'] = ['Character class is required']

        if not character.species:
            all_errors['species'] = ['Character species is required']

        if not character.background:
            all_errors['background'] = ['Character background is required']

        if not hasattr(character, 'abilities'):
            all_errors['abilities'] = ['Character ability scores are required']

        # Run specific validation checks
        if hasattr(character, 'abilities'):
            ability_scores = {
                'strength': character.abilities.strength_score,
                'dexterity': character.abilities.dexterity_score,
                'constitution': character.abilities.constitution_score,
                'intelligence': character.abilities.intelligence_score,
                'wisdom': character.abilities.wisdom_score,
                'charisma': character.abilities.charisma_score,
            }

            ability_errors = cls.validate_ability_scores(ability_scores, 'roll')
            if ability_errors:
                all_errors.update(ability_errors)

        skill_errors = cls.validate_character_skills(character)
        if skill_errors:
            all_errors.update(skill_errors)

        equipment_errors = cls.validate_character_equipment(character)
        if equipment_errors:
            all_errors.update(equipment_errors)

        spell_errors = cls.validate_character_spells(character)
        if spell_errors:
            all_errors.update(spell_errors)

        feat_errors = cls.validate_character_feats(character)
        if feat_errors:
            all_errors.update(feat_errors)

        return all_errors

    @classmethod
    def is_character_valid(cls, character: Character) -> bool:
        """
        Quick check if character is valid (no errors)
        """
        errors = cls.validate_complete_character(character)
        return len(errors) == 0

    @classmethod
    def get_character_warnings(cls, character: Character) -> Dict[str, List[str]]:
        """
        Get non-blocking warnings about character build choices

        These are suggestions/warnings that don't prevent character creation
        but might indicate suboptimal choices
        """
        warnings = {}

        if not character.dnd_class or not hasattr(character, 'abilities'):
            return warnings

        # Check if primary ability is optimized
        primary_ability = character.dnd_class.primary_ability
        primary_score = getattr(character.abilities, f"{primary_ability.lower()}_score")

        if primary_score < 14:
            warnings['suboptimal_primary'] = [
                f"{character.dnd_class.name} relies on {primary_ability.upper()}, "
                f"but your score is only {primary_score}. Consider 15+ for better effectiveness."
            ]

        # Check for very low Constitution
        con_score = character.abilities.constitution_score
        if con_score < 12:
            warnings['low_constitution'] = [
                f"Constitution of {con_score} is quite low. Consider higher CON for survivability."
            ]

        # Check for unused ASI opportunities
        if character.level >= 4:
            asi_levels = cls._get_asi_levels_for_class(character.dnd_class)
            available_asi = sum(1 for level in asi_levels if level <= character.level)
            used_asi = character.feats.exclude(source='background').count()

            # Assume remaining ASI used for ability scores, but warn if none used for feats
            if used_asi == 0 and available_asi > 0:
                warnings['no_feats'] = [
                    "Consider taking feats for additional character customization and power."
                ]

        return warnings