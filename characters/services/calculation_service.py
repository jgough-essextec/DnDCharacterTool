"""
Character Calculation Service

Handles all character stat calculations including:
- Ability modifiers
- Hit points
- Armor Class
- Attack bonuses
- Skill bonuses
- Saving throws
- Spell save DC and attack bonuses
"""
from typing import Dict, Optional, Tuple
from django.db.models import Q

from ..models import Character, CharacterAbilities, CharacterEquipment, CharacterSkill


class CharacterCalculationService:
    """Service class for calculating character statistics"""

    @staticmethod
    def calculate_ability_modifier(score: int) -> int:
        """
        Calculate ability modifier from ability score
        Formula: (score - 10) // 2
        """
        return (score - 10) // 2

    @staticmethod
    def calculate_proficiency_bonus(level: int) -> int:
        """
        Calculate proficiency bonus based on character level
        Formula: 2 + ((level - 1) // 4)
        """
        return 2 + ((level - 1) // 4)

    @classmethod
    def calculate_max_hp(cls, character: Character) -> int:
        """
        Calculate maximum hit points for a character

        Formula:
        Level 1: hit_die_max + CON_modifier + species_bonus + class_bonus
        Higher levels: Previous HP + average_hit_die + CON_modifier per level
        """
        if not character.dnd_class or not hasattr(character, 'abilities'):
            return 0

        abilities = character.abilities
        con_modifier = cls.calculate_ability_modifier(abilities.constitution_score)
        hit_die = character.dnd_class.hit_die
        level = character.level

        if level == 1:
            # Level 1: Maximum hit die + CON modifier
            max_hp = hit_die + con_modifier

            # Add species bonuses (e.g., Dwarf Toughness)
            if character.species and character.species.name == 'Dwarf':
                max_hp += level  # Dwarven Toughness: +1 HP per level

        else:
            # Calculate HP for higher levels
            # Level 1 HP + ((average_hit_die + CON_mod) * (level - 1))
            level_1_hp = hit_die + con_modifier
            average_hit_die = (hit_die // 2) + 1  # Average of hit die
            additional_levels = level - 1

            max_hp = level_1_hp + (additional_levels * (average_hit_die + con_modifier))

            # Add species bonuses
            if character.species and character.species.name == 'Dwarf':
                max_hp += level

        return max(1, max_hp)  # Minimum 1 HP

    @classmethod
    def calculate_armor_class(cls, character: Character) -> int:
        """
        Calculate Armor Class based on equipment and abilities

        Base AC calculation:
        - Unarmored: 10 + DEX modifier
        - Light Armor: armor_AC + DEX modifier
        - Medium Armor: armor_AC + min(DEX modifier, 2)
        - Heavy Armor: armor_AC (no DEX bonus)
        - Shield: +2 AC if equipped
        """
        if not hasattr(character, 'abilities'):
            return 10

        abilities = character.abilities
        dex_modifier = cls.calculate_ability_modifier(abilities.dexterity_score)

        # Start with unarmored AC
        base_ac = 10 + dex_modifier

        # Check for equipped armor
        equipped_armor = character.equipment.filter(
            equipped=True,
            equipment__armor__isnull=False
        ).select_related('equipment__armor').first()

        if equipped_armor and hasattr(equipped_armor.equipment, 'armor'):
            armor = equipped_armor.equipment.armor
            base_ac = armor.base_ac

            # Apply DEX modifier based on armor type
            if armor.armor_type == 'light':
                base_ac += dex_modifier
            elif armor.armor_type == 'medium':
                base_ac += min(dex_modifier, armor.dex_bonus_limit or 2)
            # Heavy armor gets no DEX bonus

        # Check for equipped shield
        has_shield = character.equipment.filter(
            equipped=True,
            equipment__name__icontains='shield'
        ).exists()

        if has_shield:
            base_ac += 2

        # Add any magical bonuses or class features
        # (This would be expanded based on specific items and class features)

        return base_ac

    @classmethod
    def calculate_initiative(cls, character: Character) -> int:
        """
        Calculate initiative bonus
        Formula: DEX modifier + bonuses
        """
        if not hasattr(character, 'abilities'):
            return 0

        dex_modifier = cls.calculate_ability_modifier(character.abilities.dexterity_score)
        initiative = dex_modifier

        # Add Alert feat bonus (+5 to initiative)
        if character.feats.filter(feat__name='Alert').exists():
            initiative += 5

        return initiative

    @classmethod
    def calculate_skill_bonus(cls, character: Character, skill_name: str) -> int:
        """
        Calculate skill bonus for a specific skill
        Formula: ability_modifier + proficiency_bonus (if proficient) + other bonuses
        """
        if not hasattr(character, 'abilities'):
            return 0

        try:
            character_skill = character.skills.select_related('skill').get(skill__name=skill_name)
        except CharacterSkill.DoesNotExist:
            # If skill not found, return just ability modifier
            from game_content.models import Skill
            try:
                skill = Skill.objects.get(name=skill_name)
                ability_mod = cls.calculate_ability_modifier(
                    getattr(character.abilities, f"{skill.associated_ability.lower()}_score")
                )
                return ability_mod
            except Skill.DoesNotExist:
                return 0

        return character_skill.bonus

    @classmethod
    def calculate_saving_throw_bonus(cls, character: Character, ability_name: str) -> int:
        """
        Calculate saving throw bonus for a specific ability
        Formula: ability_modifier + proficiency_bonus (if proficient)
        """
        if not hasattr(character, 'abilities'):
            return 0

        ability_modifier = cls.calculate_ability_modifier(
            getattr(character.abilities, f"{ability_name.lower()}_score")
        )

        # Check if proficient in this saving throw
        is_proficient = character.saving_throws.filter(
            ability_name=ability_name.upper(),
            is_proficient=True
        ).exists()

        if is_proficient:
            proficiency_bonus = cls.calculate_proficiency_bonus(character.level)
            return ability_modifier + proficiency_bonus

        return ability_modifier

    @classmethod
    def calculate_attack_bonus(cls, character: Character, weapon_name: str) -> Dict[str, int]:
        """
        Calculate attack bonus for a specific weapon
        Returns dict with melee and ranged bonuses
        """
        if not hasattr(character, 'abilities'):
            return {'melee': 0, 'ranged': 0}

        str_modifier = cls.calculate_ability_modifier(character.abilities.strength_score)
        dex_modifier = cls.calculate_ability_modifier(character.abilities.dexterity_score)
        proficiency_bonus = cls.calculate_proficiency_bonus(character.level)

        # Get weapon info
        try:
            weapon_equipment = character.equipment.select_related(
                'equipment__weapon'
            ).get(equipment__name=weapon_name)

            if hasattr(weapon_equipment.equipment, 'weapon'):
                weapon = weapon_equipment.equipment.weapon

                # Determine if proficient with weapon
                is_proficient = False
                weapon_proficiencies = character.dnd_class.weapon_proficiencies if character.dnd_class else []

                if weapon.weapon_category in weapon_proficiencies or 'all' in weapon_proficiencies:
                    is_proficient = True

                prof_bonus = proficiency_bonus if is_proficient else 0

                # Calculate bonuses based on weapon properties
                melee_bonus = str_modifier + prof_bonus
                ranged_bonus = dex_modifier + prof_bonus

                # Finesse weapons can use DEX for melee
                if 'finesse' in (weapon.properties or []):
                    melee_bonus = max(str_modifier, dex_modifier) + prof_bonus

                # Archery fighting style (+2 to ranged attacks)
                if character.feats.filter(feat__name='Archery').exists():
                    ranged_bonus += 2

                return {'melee': melee_bonus, 'ranged': ranged_bonus}

        except CharacterEquipment.DoesNotExist:
            pass

        # Default unarmed attack
        return {
            'melee': str_modifier + (proficiency_bonus if character.dnd_class else 0),
            'ranged': dex_modifier
        }

    @classmethod
    def calculate_spell_save_dc(cls, character: Character) -> int:
        """
        Calculate spell save DC
        Formula: 8 + proficiency_bonus + spellcasting_ability_modifier
        """
        if not character.dnd_class or not hasattr(character, 'abilities'):
            return 8

        proficiency_bonus = cls.calculate_proficiency_bonus(character.level)

        # Get spellcasting ability based on class
        spellcasting_ability = character.dnd_class.primary_ability
        ability_modifier = cls.calculate_ability_modifier(
            getattr(character.abilities, f"{spellcasting_ability.lower()}_score")
        )

        return 8 + proficiency_bonus + ability_modifier

    @classmethod
    def calculate_spell_attack_bonus(cls, character: Character) -> int:
        """
        Calculate spell attack bonus
        Formula: proficiency_bonus + spellcasting_ability_modifier
        """
        if not character.dnd_class or not hasattr(character, 'abilities'):
            return 0

        proficiency_bonus = cls.calculate_proficiency_bonus(character.level)

        # Get spellcasting ability based on class
        spellcasting_ability = character.dnd_class.primary_ability
        ability_modifier = cls.calculate_ability_modifier(
            getattr(character.abilities, f"{spellcasting_ability.lower()}_score")
        )

        return proficiency_bonus + ability_modifier

    @classmethod
    def calculate_carrying_capacity(cls, character: Character) -> Dict[str, float]:
        """
        Calculate carrying capacity in pounds

        Returns:
        - normal: STR score × 15
        - push_drag_lift: normal × 2
        - encumbered: normal / 3 (5 ft speed penalty)
        - heavily_encumbered: normal × 2/3 (10 ft speed penalty, disadvantage)
        """
        if not hasattr(character, 'abilities'):
            return {'normal': 0, 'push_drag_lift': 0, 'encumbered': 0, 'heavily_encumbered': 0}

        strength_score = character.abilities.strength_score
        normal_capacity = strength_score * 15

        return {
            'normal': normal_capacity,
            'push_drag_lift': normal_capacity * 2,
            'encumbered': normal_capacity / 3,
            'heavily_encumbered': normal_capacity * 2 / 3
        }

    @classmethod
    def calculate_current_encumbrance(cls, character: Character) -> float:
        """Calculate current total weight carried"""
        total_weight = 0.0

        for equipment in character.equipment.select_related('equipment'):
            item_weight = float(equipment.equipment.weight or 0)
            total_weight += item_weight * equipment.quantity

        return total_weight

    @classmethod
    def get_encumbrance_status(cls, character: Character) -> str:
        """
        Get encumbrance status: 'normal', 'encumbered', 'heavily_encumbered', 'overloaded'
        """
        current_weight = cls.calculate_current_encumbrance(character)
        capacity = cls.calculate_carrying_capacity(character)

        if current_weight <= capacity['encumbered']:
            return 'normal'
        elif current_weight <= capacity['heavily_encumbered']:
            return 'encumbered'
        elif current_weight <= capacity['normal']:
            return 'heavily_encumbered'
        else:
            return 'overloaded'

    @classmethod
    def calculate_all_stats(cls, character: Character) -> Dict:
        """
        Calculate all character statistics at once
        Returns a comprehensive dictionary of calculated stats
        """
        if not character or not hasattr(character, 'abilities'):
            return {}

        stats = {
            'ability_modifiers': {
                'strength': cls.calculate_ability_modifier(character.abilities.strength_score),
                'dexterity': cls.calculate_ability_modifier(character.abilities.dexterity_score),
                'constitution': cls.calculate_ability_modifier(character.abilities.constitution_score),
                'intelligence': cls.calculate_ability_modifier(character.abilities.intelligence_score),
                'wisdom': cls.calculate_ability_modifier(character.abilities.wisdom_score),
                'charisma': cls.calculate_ability_modifier(character.abilities.charisma_score),
            },
            'proficiency_bonus': cls.calculate_proficiency_bonus(character.level),
            'max_hp': cls.calculate_max_hp(character),
            'armor_class': cls.calculate_armor_class(character),
            'initiative': cls.calculate_initiative(character),
            'spell_save_dc': cls.calculate_spell_save_dc(character),
            'spell_attack_bonus': cls.calculate_spell_attack_bonus(character),
            'carrying_capacity': cls.calculate_carrying_capacity(character),
            'current_encumbrance': cls.calculate_current_encumbrance(character),
            'encumbrance_status': cls.get_encumbrance_status(character),
        }

        # Calculate saving throws
        stats['saving_throws'] = {}
        for ability in ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']:
            stats['saving_throws'][ability.lower()] = cls.calculate_saving_throw_bonus(character, ability)

        return stats