"""
Character Recommendation Service

Provides intelligent recommendations for character creation including:
- Class suggestions based on playstyle
- Background recommendations for chosen class
- Ability score optimization suggestions
- Equipment recommendations
- Spell selections for spellcasters
- Feat recommendations
- Character build synergy analysis
"""
from typing import Dict, List, Optional, Tuple, Union
from django.db.models import Q

from ..models import Character, CharacterAbilities
from game_content.models import DnDClass, Background, Species, Feat, Spell, Equipment


class RecommendationService:
    """Service class for providing character creation recommendations"""

    # Playstyle mappings for class recommendations
    PLAYSTYLE_TO_CLASSES = {
        'damage_dealer': {
            'primary': ['Fighter', 'Barbarian', 'Ranger', 'Rogue'],
            'secondary': ['Paladin', 'Warlock', 'Sorcerer']
        },
        'spellcaster': {
            'primary': ['Wizard', 'Sorcerer', 'Warlock', 'Cleric', 'Druid'],
            'secondary': ['Bard', 'Ranger', 'Paladin']
        },
        'support': {
            'primary': ['Cleric', 'Bard', 'Druid'],
            'secondary': ['Paladin', 'Ranger', 'Wizard']
        },
        'tank': {
            'primary': ['Fighter', 'Paladin', 'Barbarian'],
            'secondary': ['Cleric', 'Druid']
        },
        'sneaky': {
            'primary': ['Rogue'],
            'secondary': ['Ranger', 'Bard', 'Warlock']
        },
        'versatile': {
            'primary': ['Bard', 'Ranger'],
            'secondary': ['Fighter', 'Cleric', 'Druid']
        },
        'beginner_friendly': {
            'primary': ['Fighter', 'Barbarian', 'Rogue'],
            'secondary': ['Cleric', 'Ranger']
        }
    }

    # Class synergies with backgrounds
    CLASS_BACKGROUND_SYNERGIES = {
        'Fighter': ['Soldier', 'Guard', 'Noble', 'Folk Hero'],
        'Wizard': ['Sage', 'Hermit', 'Scribe', 'Noble'],
        'Rogue': ['Criminal', 'Charlatan', 'Entertainer', 'Urchin'],
        'Cleric': ['Acolyte', 'Hermit', 'Noble', 'Folk Hero'],
        'Ranger': ['Outlander', 'Folk Hero', 'Guide', 'Hermit'],
        'Barbarian': ['Outlander', 'Folk Hero', 'Tribal Member', 'Soldier'],
        'Bard': ['Entertainer', 'Noble', 'Charlatan', 'Guild Artisan'],
        'Druid': ['Hermit', 'Outlander', 'Folk Hero', 'Guide'],
        'Paladin': ['Noble', 'Acolyte', 'Soldier', 'Folk Hero'],
        'Sorcerer': ['Noble', 'Hermit', 'Entertainer', 'Folk Hero'],
        'Warlock': ['Charlatan', 'Hermit', 'Entertainer', 'Noble'],
        'Monk': ['Hermit', 'Acolyte', 'Folk Hero', 'Outlander']
    }

    # Species recommendations by class
    CLASS_SPECIES_SYNERGIES = {
        'Fighter': ['Human', 'Dwarf', 'Dragonborn', 'Goliath'],
        'Wizard': ['Human', 'Elf', 'Gnome', 'Tiefling'],
        'Rogue': ['Halfling', 'Elf', 'Human', 'Tiefling'],
        'Cleric': ['Human', 'Dwarf', 'Dragonborn', 'Aasimar'],
        'Ranger': ['Elf', 'Human', 'Halfling', 'Goliath'],
        'Barbarian': ['Goliath', 'Dragonborn', 'Human', 'Orc'],
        'Bard': ['Human', 'Elf', 'Halfling', 'Tiefling'],
        'Druid': ['Elf', 'Human', 'Halfling', 'Goliath'],
        'Paladin': ['Human', 'Dragonborn', 'Aasimar', 'Dwarf'],
        'Sorcerer': ['Dragonborn', 'Tiefling', 'Elf', 'Human'],
        'Warlock': ['Tiefling', 'Human', 'Elf', 'Halfling'],
        'Monk': ['Human', 'Elf', 'Halfling', 'Dragonborn']
    }

    @classmethod
    def recommend_classes_by_playstyle(cls, playstyles: List[str], experience_level: str = 'beginner') -> Dict[str, List[str]]:
        """
        Recommend classes based on preferred playstyles

        Args:
            playstyles: List of preferred playstyles
            experience_level: 'beginner', 'intermediate', 'advanced'

        Returns:
            Dict with 'primary' and 'secondary' class recommendations
        """
        primary_classes = set()
        secondary_classes = set()

        # Add beginner-friendly classes for new players
        if experience_level == 'beginner':
            playstyles = playstyles + ['beginner_friendly']

        for playstyle in playstyles:
            if playstyle in cls.PLAYSTYLE_TO_CLASSES:
                mapping = cls.PLAYSTYLE_TO_CLASSES[playstyle]
                primary_classes.update(mapping['primary'])
                secondary_classes.update(mapping['secondary'])

        # Remove primary classes from secondary list
        secondary_classes -= primary_classes

        return {
            'primary': sorted(list(primary_classes)),
            'secondary': sorted(list(secondary_classes))
        }

    @classmethod
    def recommend_background_for_class(cls, class_name: str) -> List[str]:
        """
        Recommend backgrounds that synergize well with a class

        Args:
            class_name: Name of the chosen class

        Returns:
            List of recommended background names
        """
        return cls.CLASS_BACKGROUND_SYNERGIES.get(class_name, [])

    @classmethod
    def recommend_species_for_class(cls, class_name: str) -> List[str]:
        """
        Recommend species that synergize well with a class

        Args:
            class_name: Name of the chosen class

        Returns:
            List of recommended species names
        """
        return cls.CLASS_SPECIES_SYNERGIES.get(class_name, [])

    @classmethod
    def recommend_ability_score_priority(cls, class_name: str) -> Dict[str, int]:
        """
        Recommend ability score priorities for a class

        Args:
            class_name: Name of the chosen class

        Returns:
            Dict mapping ability names to priority (1=highest, 6=lowest)
        """
        # Class ability priority mappings
        priorities = {
            'Fighter': {
                'strength': 1, 'constitution': 2, 'dexterity': 3,
                'wisdom': 4, 'charisma': 5, 'intelligence': 6
            },
            'Wizard': {
                'intelligence': 1, 'constitution': 2, 'dexterity': 3,
                'wisdom': 4, 'charisma': 5, 'strength': 6
            },
            'Rogue': {
                'dexterity': 1, 'constitution': 2, 'intelligence': 3,
                'wisdom': 4, 'charisma': 5, 'strength': 6
            },
            'Cleric': {
                'wisdom': 1, 'constitution': 2, 'strength': 3,
                'charisma': 4, 'dexterity': 5, 'intelligence': 6
            },
            'Ranger': {
                'dexterity': 1, 'wisdom': 2, 'constitution': 3,
                'strength': 4, 'charisma': 5, 'intelligence': 6
            },
            'Barbarian': {
                'strength': 1, 'constitution': 2, 'dexterity': 3,
                'wisdom': 4, 'charisma': 5, 'intelligence': 6
            },
            'Bard': {
                'charisma': 1, 'dexterity': 2, 'constitution': 3,
                'wisdom': 4, 'intelligence': 5, 'strength': 6
            },
            'Druid': {
                'wisdom': 1, 'constitution': 2, 'dexterity': 3,
                'strength': 4, 'intelligence': 5, 'charisma': 6
            },
            'Paladin': {
                'strength': 1, 'charisma': 2, 'constitution': 3,
                'wisdom': 4, 'dexterity': 5, 'intelligence': 6
            },
            'Sorcerer': {
                'charisma': 1, 'constitution': 2, 'dexterity': 3,
                'wisdom': 4, 'intelligence': 5, 'strength': 6
            },
            'Warlock': {
                'charisma': 1, 'constitution': 2, 'dexterity': 3,
                'wisdom': 4, 'intelligence': 5, 'strength': 6
            },
            'Monk': {
                'dexterity': 1, 'wisdom': 2, 'constitution': 3,
                'strength': 4, 'intelligence': 5, 'charisma': 6
            }
        }

        return priorities.get(class_name, {})

    @classmethod
    def recommend_ability_score_assignment(cls, class_name: str, scores: List[int]) -> Dict[str, int]:
        """
        Recommend how to assign rolled/standard array ability scores

        Args:
            class_name: Name of the chosen class
            scores: List of 6 ability scores to assign

        Returns:
            Dict mapping ability names to recommended scores
        """
        priorities = cls.recommend_ability_score_priority(class_name)
        sorted_scores = sorted(scores, reverse=True)

        # Create ability list sorted by priority
        abilities_by_priority = sorted(priorities.items(), key=lambda x: x[1])

        assignment = {}
        for i, (ability, _) in enumerate(abilities_by_priority):
            if i < len(sorted_scores):
                assignment[ability] = sorted_scores[i]

        return assignment

    @classmethod
    def recommend_starting_equipment(cls, character: Character) -> Dict[str, List[str]]:
        """
        Recommend starting equipment for a character

        Args:
            character: Character object with class and background

        Returns:
            Dict with equipment recommendations by category
        """
        recommendations = {
            'weapons': [],
            'armor': [],
            'tools': [],
            'other': []
        }

        if not character.dnd_class:
            return recommendations

        class_name = character.dnd_class.name

        # Class-specific weapon recommendations
        weapon_recommendations = {
            'Fighter': ['Longsword', 'Shield', 'Crossbow, light', 'Handaxe'],
            'Wizard': ['Quarterstaff', 'Dagger', 'Crossbow, light'],
            'Rogue': ['Shortsword', 'Shortbow', 'Dagger', 'Thieves\' tools'],
            'Cleric': ['Mace', 'Shield', 'Scale mail', 'Crossbow, light'],
            'Ranger': ['Longsword', 'Longbow', 'Studded leather armor'],
            'Barbarian': ['Greataxe', 'Handaxe', 'Javelin'],
            'Bard': ['Rapier', 'Shortbow', 'Leather armor'],
            'Druid': ['Scimitar', 'Shield', 'Leather armor'],
            'Paladin': ['Longsword', 'Shield', 'Chain mail'],
            'Sorcerer': ['Quarterstaff', 'Dagger', 'Crossbow, light'],
            'Warlock': ['Shortsword', 'Crossbow, light', 'Leather armor'],
            'Monk': ['Shortsword', 'Dart', 'Simple weapon']
        }

        recommendations['weapons'] = weapon_recommendations.get(class_name, [])

        # Add background-specific tools
        if character.background:
            background_tools = {
                'Acolyte': ['Holy symbol'],
                'Criminal': ['Thieves\' tools', 'Crowbar'],
                'Entertainer': ['Musical instrument', 'Costume'],
                'Folk Hero': ['Smith\'s tools', 'Vehicles (land)'],
                'Noble': ['Gaming set', 'Signet ring'],
                'Sage': ['Ink and quill', 'Parchment'],
                'Soldier': ['Gaming set', 'Vehicles (land)']
            }

            background_name = character.background.name
            recommendations['tools'] = background_tools.get(background_name, [])

        # General adventuring gear
        recommendations['other'] = [
            'Backpack', 'Bedroll', 'Rations (10 days)',
            'Rope (50 feet)', 'Torch (10)', 'Tinderbox'
        ]

        return recommendations

    @classmethod
    def recommend_spells_for_class(cls, class_name: str, level: int = 1,
                                 spell_level: int = 1) -> List[Dict[str, str]]:
        """
        Recommend essential spells for a spellcasting class

        Args:
            class_name: Name of the spellcasting class
            level: Character level
            spell_level: Spell level to recommend

        Returns:
            List of spell recommendations with reasons
        """
        # Essential spell recommendations by class
        spell_recommendations = {
            'Wizard': {
                0: [  # Cantrips
                    {'name': 'Mage Hand', 'reason': 'Utility cantrip for manipulation'},
                    {'name': 'Minor Illusion', 'reason': 'Versatile for creativity'},
                    {'name': 'Fire Bolt', 'reason': 'Reliable damage cantrip'}
                ],
                1: [
                    {'name': 'Shield', 'reason': 'Essential defensive spell'},
                    {'name': 'Magic Missile', 'reason': 'Guaranteed damage'},
                    {'name': 'Detect Magic', 'reason': 'Utility for finding magic'}
                ]
            },
            'Cleric': {
                0: [
                    {'name': 'Sacred Flame', 'reason': 'Dexterity save damage'},
                    {'name': 'Guidance', 'reason': 'Help allies with skill checks'},
                    {'name': 'Thaumaturgy', 'reason': 'Impressive divine effects'}
                ],
                1: [
                    {'name': 'Cure Wounds', 'reason': 'Essential healing'},
                    {'name': 'Bless', 'reason': 'Boost allies\' attacks and saves'},
                    {'name': 'Guiding Bolt', 'reason': 'Damage with utility'}
                ]
            },
            'Sorcerer': {
                0: [
                    {'name': 'Fire Bolt', 'reason': 'Reliable damage cantrip'},
                    {'name': 'Mage Hand', 'reason': 'Useful utility'},
                    {'name': 'Minor Illusion', 'reason': 'Creative problem solving'}
                ],
                1: [
                    {'name': 'Shield', 'reason': 'Critical defensive spell'},
                    {'name': 'Magic Missile', 'reason': 'Guaranteed damage'},
                    {'name': 'Chromatic Orb', 'reason': 'Flexible damage type'}
                ]
            },
            'Warlock': {
                0: [
                    {'name': 'Eldritch Blast', 'reason': 'Core warlock damage cantrip'},
                    {'name': 'Minor Illusion', 'reason': 'Versatile utility'},
                    {'name': 'Prestidigitation', 'reason': 'Useful minor effects'}
                ],
                1: [
                    {'name': 'Hex', 'reason': 'Boost damage and debuff'},
                    {'name': 'Armor of Agathys', 'reason': 'Temp HP and damage'},
                    {'name': 'Charm Person', 'reason': 'Social manipulation'}
                ]
            },
            'Bard': {
                0: [
                    {'name': 'Vicious Mockery', 'reason': 'Damage with debuff'},
                    {'name': 'Minor Illusion', 'reason': 'Creative utility'},
                    {'name': 'Mage Hand', 'reason': 'Useful manipulation'}
                ],
                1: [
                    {'name': 'Healing Word', 'reason': 'Bonus action healing'},
                    {'name': 'Faerie Fire', 'reason': 'Great debuff spell'},
                    {'name': 'Dissonant Whispers', 'reason': 'Damage with movement'}
                ]
            },
            'Druid': {
                0: [
                    {'name': 'Produce Flame', 'reason': 'Damage and light source'},
                    {'name': 'Guidance', 'reason': 'Help with skill checks'},
                    {'name': 'Druidcraft', 'reason': 'Nature-themed utility'}
                ],
                1: [
                    {'name': 'Cure Wounds', 'reason': 'Essential healing'},
                    {'name': 'Entangle', 'reason': 'Area control'},
                    {'name': 'Goodberry', 'reason': 'Healing and sustenance'}
                ]
            }
        }

        return spell_recommendations.get(class_name, {}).get(spell_level, [])

    @classmethod
    def recommend_feats_for_build(cls, character: Character) -> List[Dict[str, str]]:
        """
        Recommend feats that synergize with character build

        Args:
            character: Character object

        Returns:
            List of feat recommendations with reasons
        """
        if not character.dnd_class or not hasattr(character, 'abilities'):
            return []

        recommendations = []
        class_name = character.dnd_class.name

        # Class-specific feat recommendations
        class_feats = {
            'Fighter': [
                {'name': 'Great Weapon Master', 'reason': 'Massive damage for two-handed weapons'},
                {'name': 'Sharpshooter', 'reason': 'Enhanced ranged combat'},
                {'name': 'Sentinel', 'reason': 'Control battlefield movement'},
                {'name': 'Polearm Master', 'reason': 'Extra attacks with polearms'}
            ],
            'Wizard': [
                {'name': 'Telekinetic', 'reason': 'Enhanced battlefield control'},
                {'name': 'War Caster', 'reason': 'Cast spells in armor with weapons'},
                {'name': 'Resilient (Constitution)', 'reason': 'Better concentration saves'},
                {'name': 'Fey Touched', 'reason': 'Extra spells and teleportation'}
            ],
            'Rogue': [
                {'name': 'Sharpshooter', 'reason': 'Enhanced sneak attack damage at range'},
                {'name': 'Alert', 'reason': 'Always act first, avoid surprise'},
                {'name': 'Lucky', 'reason': 'Reroll failed important rolls'},
                {'name': 'Mobile', 'reason': 'Hit and run tactics'}
            ],
            'Cleric': [
                {'name': 'War Caster', 'reason': 'Cast with shield and weapon'},
                {'name': 'Resilient (Wisdom)', 'reason': 'Better wisdom saves'},
                {'name': 'Spiritual Weapon', 'reason': 'Bonus action attacks'},
                {'name': 'Lucky', 'reason': 'Reroll important saves and attacks'}
            ],
            'Barbarian': [
                {'name': 'Great Weapon Master', 'reason': 'Massive damage while raging'},
                {'name': 'Sentinel', 'reason': 'Protect allies and control enemies'},
                {'name': 'Mobile', 'reason': 'Enhanced movement and positioning'},
                {'name': 'Tough', 'reason': 'Even more hit points'}
            ]
        }

        # Get class-specific recommendations
        class_recommendations = class_feats.get(class_name, [])
        recommendations.extend(class_recommendations)

        # Add general good feats
        general_feats = [
            {'name': 'Lucky', 'reason': 'Universally useful rerolls'},
            {'name': 'Alert', 'reason': 'Better initiative and avoid surprise'},
            {'name': 'Tough', 'reason': 'Increased survivability'}
        ]

        # Only add general feats not already recommended
        recommended_names = {rec['name'] for rec in recommendations}
        for feat in general_feats:
            if feat['name'] not in recommended_names:
                recommendations.append(feat)

        return recommendations[:6]  # Return top 6 recommendations

    @classmethod
    def analyze_character_synergies(cls, character: Character) -> Dict[str, List[str]]:
        """
        Analyze synergies in current character build

        Args:
            character: Character object to analyze

        Returns:
            Dict with 'strengths', 'weaknesses', and 'suggestions'
        """
        analysis = {
            'strengths': [],
            'weaknesses': [],
            'suggestions': []
        }

        if not character.dnd_class or not hasattr(character, 'abilities'):
            analysis['weaknesses'].append('Character build incomplete')
            return analysis

        class_name = character.dnd_class.name
        abilities = character.abilities

        # Analyze ability score allocation
        primary_ability = character.dnd_class.primary_ability
        primary_score = getattr(abilities, f"{primary_ability.lower()}_score")

        if primary_score >= 15:
            analysis['strengths'].append(f"Strong {primary_ability} ({primary_score}) for {class_name}")
        elif primary_score < 13:
            analysis['weaknesses'].append(f"Low {primary_ability} ({primary_score}) may hurt effectiveness")

        # Constitution check
        con_score = abilities.constitution_score
        if con_score >= 14:
            analysis['strengths'].append(f"Good Constitution ({con_score}) for survivability")
        elif con_score < 12:
            analysis['weaknesses'].append(f"Low Constitution ({con_score}) reduces hit points")
            analysis['suggestions'].append("Consider increasing Constitution at next ASI")

        # Class-specific analysis
        if class_name == 'Fighter':
            str_score = abilities.strength_score
            dex_score = abilities.dexterity_score

            if str_score >= 15 and dex_score >= 13:
                analysis['strengths'].append("Well-rounded combat abilities")
            elif str_score >= 15:
                analysis['strengths'].append("Strong melee combat potential")
            elif dex_score >= 15:
                analysis['strengths'].append("Good ranged combat and AC")

        elif class_name in ['Wizard', 'Sorcerer', 'Warlock']:
            dex_score = abilities.dexterity_score
            if dex_score >= 14:
                analysis['strengths'].append("Good Dexterity for AC and initiative")
            else:
                analysis['suggestions'].append("Consider Mage Armor spell for better AC")

        # Background synergy
        if character.background:
            recommended_backgrounds = cls.recommend_background_for_class(class_name)
            if character.background.name in recommended_backgrounds:
                analysis['strengths'].append(f"{character.background.name} background synergizes well with {class_name}")

        # Species synergy
        if character.species:
            recommended_species = cls.recommend_species_for_class(class_name)
            if character.species.name in recommended_species:
                analysis['strengths'].append(f"{character.species.name} species complements {class_name} abilities")

        # Equipment recommendations
        if hasattr(character, 'equipment'):
            equipped_armor = character.equipment.filter(
                equipped=True,
                equipment__armor__isnull=False
            ).first()

            if not equipped_armor and class_name not in ['Barbarian', 'Monk']:
                analysis['suggestions'].append("Consider equipping armor for better AC")

        return analysis

    @classmethod
    def get_build_optimization_score(cls, character: Character) -> Dict[str, Union[int, str]]:
        """
        Calculate an optimization score for the character build

        Args:
            character: Character to evaluate

        Returns:
            Dict with score (0-100) and grade (A-F)
        """
        if not character.dnd_class or not hasattr(character, 'abilities'):
            return {'score': 0, 'grade': 'F', 'reason': 'Incomplete character'}

        score = 0
        max_score = 100

        # Primary ability optimization (30 points)
        primary_ability = character.dnd_class.primary_ability
        primary_score = getattr(character.abilities, f"{primary_ability.lower()}_score")

        if primary_score >= 15:
            score += 30
        elif primary_score >= 13:
            score += 20
        elif primary_score >= 10:
            score += 10

        # Constitution optimization (20 points)
        con_score = character.abilities.constitution_score
        if con_score >= 14:
            score += 20
        elif con_score >= 12:
            score += 15
        elif con_score >= 10:
            score += 10

        # Background synergy (15 points)
        if character.background:
            recommended_backgrounds = cls.recommend_background_for_class(character.dnd_class.name)
            if character.background.name in recommended_backgrounds:
                score += 15

        # Species synergy (15 points)
        if character.species:
            recommended_species = cls.recommend_species_for_class(character.dnd_class.name)
            if character.species.name in recommended_species:
                score += 15

        # Balanced ability scores (10 points)
        all_scores = [
            character.abilities.strength_score,
            character.abilities.dexterity_score,
            character.abilities.constitution_score,
            character.abilities.intelligence_score,
            character.abilities.wisdom_score,
            character.abilities.charisma_score
        ]

        # Check for no dump stats (no scores below 8)
        if all(score >= 8 for score in all_scores):
            score += 10

        # Skills optimization (10 points)
        # This would check if character has optimal skill selections
        # Simplified for now
        if hasattr(character, 'skills') and character.skills.exists():
            score += 10

        # Determine grade
        if score >= 90:
            grade = 'A+'
        elif score >= 80:
            grade = 'A'
        elif score >= 70:
            grade = 'B'
        elif score >= 60:
            grade = 'C'
        elif score >= 50:
            grade = 'D'
        else:
            grade = 'F'

        return {
            'score': score,
            'grade': grade,
            'max_score': max_score,
            'percentage': int((score / max_score) * 100)
        }