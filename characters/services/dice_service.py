"""
Dice Rolling Service

Handles all dice rolling functionality including:
- Basic dice notation (XdY+Z)
- Ability score generation (4d6 drop lowest)
- Advantage/Disadvantage rolls
- Attack rolls and damage
- Saving throws and skill checks
"""
import random
import re
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass


@dataclass
class DiceRoll:
    """Represents a single dice roll result"""
    dice_count: int
    dice_size: int
    modifier: int
    individual_rolls: List[int]
    total: int
    description: str

    def __str__(self):
        return f"{self.description}: {self.total}"


@dataclass
class AdvantageRoll:
    """Represents an advantage/disadvantage roll (2d20, take higher/lower)"""
    roll1: int
    roll2: int
    result: int
    advantage_type: str  # 'advantage', 'disadvantage', 'normal'
    description: str

    def __str__(self):
        if self.advantage_type == 'advantage':
            return f"{self.description} (Advantage): [{self.roll1}, {self.roll2}] → {self.result}"
        elif self.advantage_type == 'disadvantage':
            return f"{self.description} (Disadvantage): [{self.roll1}, {self.roll2}] → {self.result}"
        else:
            return f"{self.description}: {self.result}"


class DiceRollerService:
    """Service class for all dice rolling operations"""

    @staticmethod
    def roll_die(sides: int) -> int:
        """Roll a single die with specified number of sides"""
        if sides < 1:
            raise ValueError("Die must have at least 1 side")
        return random.randint(1, sides)

    @classmethod
    def roll_dice(cls, count: int, sides: int, modifier: int = 0,
                  drop_lowest: int = 0, drop_highest: int = 0) -> DiceRoll:
        """
        Roll multiple dice with optional modifiers and drop rules

        Args:
            count: Number of dice to roll
            sides: Number of sides on each die
            modifier: Fixed modifier to add to total
            drop_lowest: Number of lowest dice to drop
            drop_highest: Number of highest dice to drop

        Returns:
            DiceRoll object with full results
        """
        if count < 1:
            raise ValueError("Must roll at least 1 die")
        if sides < 1:
            raise ValueError("Die must have at least 1 side")
        if drop_lowest + drop_highest >= count:
            raise ValueError("Cannot drop more dice than rolled")

        # Roll all dice
        rolls = [cls.roll_die(sides) for _ in range(count)]
        original_rolls = rolls.copy()

        # Apply drop rules
        if drop_lowest > 0:
            rolls_sorted = sorted(rolls)
            rolls = rolls_sorted[drop_lowest:]

        if drop_highest > 0:
            rolls_sorted = sorted(rolls, reverse=True)
            rolls = rolls_sorted[drop_highest:]

        # Calculate total
        dice_total = sum(rolls)
        final_total = dice_total + modifier

        # Create description
        description_parts = [f"{count}d{sides}"]
        if drop_lowest > 0:
            description_parts.append(f"drop lowest {drop_lowest}")
        if drop_highest > 0:
            description_parts.append(f"drop highest {drop_highest}")
        if modifier > 0:
            description_parts.append(f"+{modifier}")
        elif modifier < 0:
            description_parts.append(str(modifier))

        description = " ".join(description_parts)

        return DiceRoll(
            dice_count=count,
            dice_size=sides,
            modifier=modifier,
            individual_rolls=original_rolls,
            total=final_total,
            description=description
        )

    @classmethod
    def parse_dice_notation(cls, notation: str) -> DiceRoll:
        """
        Parse standard dice notation like "3d6+2", "1d20", "2d8-1"

        Supported formats:
        - XdY (e.g., "3d6", "1d20")
        - XdY+Z (e.g., "3d6+2", "1d20+5")
        - XdY-Z (e.g., "2d8-1")
        """
        notation = notation.strip().lower().replace(" ", "")

        # Pattern: optional number, 'd', number, optional +/- number
        pattern = r'^(\d+)?d(\d+)([+-]\d+)?$'
        match = re.match(pattern, notation)

        if not match:
            raise ValueError(f"Invalid dice notation: {notation}")

        count_str, sides_str, modifier_str = match.groups()

        count = int(count_str) if count_str else 1
        sides = int(sides_str)
        modifier = int(modifier_str) if modifier_str else 0

        return cls.roll_dice(count, sides, modifier)

    @classmethod
    def roll_ability_score(cls) -> DiceRoll:
        """
        Roll ability score using 4d6, drop lowest method

        Returns:
            DiceRoll with the result (typically 3-18)
        """
        return cls.roll_dice(4, 6, drop_lowest=1)

    @classmethod
    def roll_ability_scores(cls, count: int = 6) -> List[DiceRoll]:
        """
        Roll multiple ability scores

        Args:
            count: Number of ability scores to roll (default 6 for STR, DEX, CON, INT, WIS, CHA)

        Returns:
            List of DiceRoll objects
        """
        return [cls.roll_ability_score() for _ in range(count)]

    @classmethod
    def roll_standard_ability_scores(cls) -> Dict[str, DiceRoll]:
        """
        Roll all six ability scores with labels

        Returns:
            Dict mapping ability names to DiceRoll results
        """
        abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        rolls = cls.roll_ability_scores(6)

        return dict(zip(abilities, rolls))

    @classmethod
    def roll_with_advantage(cls, sides: int = 20, modifier: int = 0,
                           advantage_type: str = 'advantage') -> AdvantageRoll:
        """
        Roll with advantage or disadvantage (2d20, take higher/lower)

        Args:
            sides: Die size (usually 20)
            modifier: Modifier to add to final result
            advantage_type: 'advantage', 'disadvantage', or 'normal'

        Returns:
            AdvantageRoll object
        """
        roll1 = cls.roll_die(sides)
        roll2 = cls.roll_die(sides) if advantage_type != 'normal' else roll1

        if advantage_type == 'advantage':
            result = max(roll1, roll2) + modifier
            description = f"1d{sides} with advantage"
        elif advantage_type == 'disadvantage':
            result = min(roll1, roll2) + modifier
            description = f"1d{sides} with disadvantage"
        else:
            result = roll1 + modifier
            description = f"1d{sides}"

        if modifier != 0:
            if modifier > 0:
                description += f" +{modifier}"
            else:
                description += f" {modifier}"

        return AdvantageRoll(
            roll1=roll1,
            roll2=roll2,
            result=result,
            advantage_type=advantage_type,
            description=description
        )

    @classmethod
    def roll_attack(cls, attack_bonus: int, advantage_type: str = 'normal') -> AdvantageRoll:
        """
        Roll an attack roll (d20 + attack bonus)

        Args:
            attack_bonus: Attack bonus to add
            advantage_type: 'advantage', 'disadvantage', or 'normal'

        Returns:
            AdvantageRoll object
        """
        roll = cls.roll_with_advantage(20, attack_bonus, advantage_type)
        roll.description = f"Attack roll ({roll.description})"
        return roll

    @classmethod
    def roll_saving_throw(cls, save_bonus: int, dc: int, advantage_type: str = 'normal') -> Tuple[AdvantageRoll, bool]:
        """
        Roll a saving throw against a DC

        Args:
            save_bonus: Saving throw bonus
            dc: Difficulty Class to beat
            advantage_type: 'advantage', 'disadvantage', or 'normal'

        Returns:
            Tuple of (AdvantageRoll, success: bool)
        """
        roll = cls.roll_with_advantage(20, save_bonus, advantage_type)
        roll.description = f"Saving throw ({roll.description})"
        success = roll.result >= dc
        return roll, success

    @classmethod
    def roll_skill_check(cls, skill_bonus: int, dc: int, advantage_type: str = 'normal') -> Tuple[AdvantageRoll, bool]:
        """
        Roll a skill check against a DC

        Args:
            skill_bonus: Skill bonus to add
            dc: Difficulty Class to beat
            advantage_type: 'advantage', 'disadvantage', or 'normal'

        Returns:
            Tuple of (AdvantageRoll, success: bool)
        """
        roll = cls.roll_with_advantage(20, skill_bonus, advantage_type)
        roll.description = f"Skill check ({roll.description})"
        success = roll.result >= dc
        return roll, success

    @classmethod
    def roll_damage(cls, damage_dice: str, damage_type: str = '') -> DiceRoll:
        """
        Roll weapon or spell damage

        Args:
            damage_dice: Dice notation like "1d8+3" or "2d6"
            damage_type: Type of damage (slashing, fire, etc.)

        Returns:
            DiceRoll object
        """
        roll = cls.parse_dice_notation(damage_dice)
        if damage_type:
            roll.description = f"{damage_dice} {damage_type} damage"
        else:
            roll.description = f"{damage_dice} damage"
        return roll

    @classmethod
    def roll_initiative(cls, initiative_bonus: int) -> int:
        """
        Roll initiative (d20 + DEX modifier + bonuses)

        Args:
            initiative_bonus: Total initiative bonus

        Returns:
            Initiative result
        """
        roll = cls.roll_dice(1, 20, initiative_bonus)
        return roll.total

    @classmethod
    def roll_hit_points(cls, hit_die: int, con_modifier: int, level: int = 1) -> int:
        """
        Roll hit points for level up

        Args:
            hit_die: Class hit die (d6, d8, d10, d12)
            con_modifier: Constitution modifier
            level: Character level (for multiple rolls)

        Returns:
            Total HP rolled
        """
        if level == 1:
            # Level 1 always gets max HP
            return hit_die + con_modifier

        total_hp = hit_die + con_modifier  # Level 1 HP

        # Roll for additional levels
        for _ in range(level - 1):
            roll = cls.roll_dice(1, hit_die, con_modifier)
            total_hp += max(1, roll.total)  # Minimum 1 HP per level

        return total_hp

    @classmethod
    def simulate_ability_score_arrays(cls, iterations: int = 1000) -> Dict[str, float]:
        """
        Simulate rolling ability scores to get statistics

        Args:
            iterations: Number of simulations to run

        Returns:
            Dict with statistics (average, min, max, etc.)
        """
        all_totals = []
        all_individual = []

        for _ in range(iterations):
            rolls = cls.roll_ability_scores(6)
            totals = [roll.total for roll in rolls]
            all_totals.append(sum(totals))
            all_individual.extend(totals)

        return {
            'average_total': sum(all_totals) / len(all_totals),
            'min_total': min(all_totals),
            'max_total': max(all_totals),
            'average_individual': sum(all_individual) / len(all_individual),
            'min_individual': min(all_individual),
            'max_individual': max(all_individual),
            'iterations': iterations
        }

    @classmethod
    def get_point_buy_equivalent(cls, rolled_scores: List[int]) -> Dict[str, Union[int, bool]]:
        """
        Calculate point buy cost for rolled ability scores

        Args:
            rolled_scores: List of 6 ability scores

        Returns:
            Dict with point buy analysis
        """
        # Point buy costs: 8=0, 9=1, 10=2, 11=3, 12=4, 13=5, 14=7, 15=9
        cost_table = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}

        total_cost = 0
        valid_for_point_buy = True

        for score in rolled_scores:
            if score < 8 or score > 15:
                valid_for_point_buy = False
                break
            total_cost += cost_table.get(score, 0)

        return {
            'total_cost': total_cost,
            'valid_for_point_buy': valid_for_point_buy,
            'exceeds_point_buy': total_cost > 27,
            'point_buy_limit': 27
        }

    @classmethod
    def roll_random_table(cls, table: Dict[Union[int, Tuple[int, int]], str],
                         die_size: int = 100) -> Tuple[int, str]:
        """
        Roll on a random table

        Args:
            table: Dict mapping roll ranges to results
            die_size: Size of die to roll

        Returns:
            Tuple of (roll_result, table_result)
        """
        roll = cls.roll_die(die_size)

        for key, value in table.items():
            if isinstance(key, tuple):
                min_roll, max_roll = key
                if min_roll <= roll <= max_roll:
                    return roll, value
            elif isinstance(key, int):
                if roll == key:
                    return roll, value

        # If no match found, return the roll and empty result
        return roll, ""

    @classmethod
    def generate_character_name(cls, species: str = 'Human', gender: str = 'any') -> str:
        """
        Generate a random D&D character name

        Args:
            species: Character species/race
            gender: 'male', 'female', or 'any'

        Returns:
            Random character name
        """
        # Simple name generation - in a real implementation,
        # this would use extensive name tables
        human_names = {
            'male': ['Aerdyn', 'Beiro', 'Carric', 'Drannor', 'Enna', 'Galinndan'],
            'female': ['Adrie', 'Birel', 'Caelynn', 'Dayereth', 'Enna', 'Galinndan']
        }

        if species.lower() == 'human':
            if gender in human_names:
                names = human_names[gender]
            else:
                names = human_names['male'] + human_names['female']

            return random.choice(names)

        # Default random name
        syllables = ['ad', 'al', 'am', 'an', 'ar', 'ea', 'el', 'er', 'in', 'on', 'or', 'ou']
        name_length = random.randint(2, 3)
        name = ''.join(random.choices(syllables, k=name_length))
        return name.capitalize()

    @classmethod
    def validate_dice_notation(cls, notation: str) -> bool:
        """
        Validate dice notation without rolling

        Args:
            notation: Dice notation string

        Returns:
            True if valid notation
        """
        try:
            notation = notation.strip().lower().replace(" ", "")
            pattern = r'^(\d+)?d(\d+)([+-]\d+)?$'
            return bool(re.match(pattern, notation))
        except:
            return False