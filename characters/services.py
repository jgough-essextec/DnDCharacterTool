"""
Character validation and additional services for D&D Character Creator
"""

from typing import Dict, List
from .models import Character


class CharacterValidationService:
    """
    Service for validating character builds and ensuring rules compliance
    """

    def __init__(self, character: Character):
        self.character = character

    def validate_character(self) -> Dict[str, List[str]]:
        """
        Validate entire character build and return any errors
        Returns dict with error categories as keys and lists of error messages as values
        """
        errors = {
            'abilities': [],
            'skills': [],
            'spells': [],
            'equipment': [],
            'general': []
        }

        errors['abilities'].extend(self._validate_ability_scores())
        errors['skills'].extend(self._validate_skills())
        errors['spells'].extend(self._validate_spells())
        errors['equipment'].extend(self._validate_equipment())
        errors['general'].extend(self._validate_general_rules())

        # Remove empty error categories
        return {k: v for k, v in errors.items() if v}

    def _validate_ability_scores(self) -> List[str]:
        """Validate ability scores are within acceptable ranges"""
        errors = []

        if not self.character.abilities:
            errors.append("Character must have ability scores assigned")
            return errors

        abilities = self.character.abilities
        for ability_name, score in [
            ('Strength', abilities.strength_score),
            ('Dexterity', abilities.dexterity_score),
            ('Constitution', abilities.constitution_score),
            ('Intelligence', abilities.intelligence_score),
            ('Wisdom', abilities.wisdom_score),
            ('Charisma', abilities.charisma_score),
        ]:
            if score < 3 or score > 20:
                errors.append(f"{ability_name} score ({score}) must be between 3 and 20")

        return errors

    def _validate_skills(self) -> List[str]:
        """Validate skill selections match class requirements"""
        errors = []

        if not self.character.dnd_class:
            return errors

        # TODO: Implement class-specific skill validation
        # Check number of proficient skills matches class requirements

        return errors

    def _validate_spells(self) -> List[str]:
        """Validate spell selections are valid for character"""
        errors = []

        if not self.character.dnd_class:
            return errors

        # TODO: Implement spell validation
        # - Spells are from class spell list
        # - Number of spells known/prepared is correct
        # - Spell levels are appropriate for character level

        return errors

    def _validate_equipment(self) -> List[str]:
        """Validate equipment proficiency and encumbrance"""
        errors = []

        # TODO: Implement equipment validation
        # - Character is proficient with equipped armor/weapons
        # - Carrying capacity not exceeded

        return errors

    def _validate_general_rules(self) -> List[str]:
        """Validate general D&D rules compliance"""
        errors = []

        if self.character.level < 1 or self.character.level > 20:
            errors.append(f"Character level ({self.character.level}) must be between 1 and 20")

        if not self.character.dnd_class:
            errors.append("Character must have a class selected")

        if not self.character.species:
            errors.append("Character must have a species selected")

        return errors


