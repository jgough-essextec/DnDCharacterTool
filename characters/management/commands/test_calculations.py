"""
Management command to test character calculation services
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from characters.models import Character, CharacterAbilities
from characters.services.calculation_service import CharacterCalculationService
from characters.services.dice_service import DiceRollerService
from game_content.models import DnDClass, Species

User = get_user_model()


class Command(BaseCommand):
    help = 'Test character calculation services'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-character',
            action='store_true',
            help='Create a test character for calculations',
        )
        parser.add_argument(
            '--test-dice',
            action='store_true',
            help='Test dice rolling functionality',
        )

    def handle(self, *args, **options):
        if options['create_test_character']:
            self.create_test_character()

        if options['test_dice']:
            self.test_dice_rolling()

        # Test calculations on existing characters
        self.test_character_calculations()

    def create_test_character(self):
        """Create a test character for calculation testing"""
        self.stdout.write("Creating test character...")

        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='test_calc_user',
            defaults={'email': 'test@example.com'}
        )

        # Get first available class and species
        dnd_class = DnDClass.objects.first()
        species = Species.objects.first()

        # Create test character
        character, created = Character.objects.get_or_create(
            user=user,
            character_name='Test Calculator',
            defaults={
                'level': 5,
                'dnd_class': dnd_class,
                'species': species,
            }
        )

        # Create abilities if not exist
        abilities, created = CharacterAbilities.objects.get_or_create(
            character=character,
            defaults={
                'strength_score': 16,
                'dexterity_score': 14,
                'constitution_score': 15,
                'intelligence_score': 12,
                'wisdom_score': 13,
                'charisma_score': 8,
            }
        )

        self.stdout.write(
            self.style.SUCCESS(f'Test character created/updated: {character}')
        )

    def test_character_calculations(self):
        """Test calculation services on existing characters"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("TESTING CHARACTER CALCULATIONS")
        self.stdout.write("="*50)

        characters = Character.objects.all()[:3]  # Test first 3 characters

        if not characters:
            self.stdout.write(
                self.style.WARNING('No characters found. Create some characters first.')
            )
            return

        for character in characters:
            self.stdout.write(f"\n--- Testing {character} ---")

            # Basic calculations
            self.stdout.write(f"Level: {character.level}")
            self.stdout.write(f"Proficiency Bonus: {CharacterCalculationService.calculate_proficiency_bonus(character.level)}")

            if character.abilities:
                self.stdout.write("Ability Scores & Modifiers:")
                abilities = character.abilities
                for ability, score in [
                    ('STR', abilities.strength_score),
                    ('DEX', abilities.dexterity_score),
                    ('CON', abilities.constitution_score),
                    ('INT', abilities.intelligence_score),
                    ('WIS', abilities.wisdom_score),
                    ('CHA', abilities.charisma_score),
                ]:
                    modifier = CharacterCalculationService.calculate_ability_modifier(score)
                    self.stdout.write(f"  {ability}: {score} ({modifier:+d})")

                # Combat stats
                self.stdout.write("Combat Statistics:")
                max_hp = CharacterCalculationService.calculate_max_hp(character)
                ac = CharacterCalculationService.calculate_armor_class(character)
                initiative = CharacterCalculationService.calculate_initiative(character)

                self.stdout.write(f"  Max HP: {max_hp}")
                self.stdout.write(f"  Armor Class: {ac}")
                self.stdout.write(f"  Initiative: {initiative:+d}")

                # Spellcasting (if applicable)
                if character.dnd_class and hasattr(character.dnd_class, 'primary_ability'):
                    self.stdout.write("Spellcasting:")
                    spell_save_dc = CharacterCalculationService.calculate_spell_save_dc(character)
                    spell_attack = CharacterCalculationService.calculate_spell_attack_bonus(character)

                    self.stdout.write(f"  Spell Save DC: {spell_save_dc}")
                    self.stdout.write(f"  Spell Attack Bonus: {spell_attack:+d}")

                # Utility
                carrying_capacity = CharacterCalculationService.calculate_carrying_capacity(character)
                self.stdout.write(f"Carrying Capacity: {carrying_capacity}")

                # Complete stats
                self.stdout.write("\nComplete Stats Summary:")
                complete_stats = CharacterCalculationService.calculate_all_stats(character)
                for category, stats in complete_stats.items():
                    if isinstance(stats, dict):
                        self.stdout.write(f"  {category.title()}: {stats}")
                    else:
                        self.stdout.write(f"  {category.title()}: {stats}")

            else:
                self.stdout.write(
                    self.style.WARNING(f"No abilities set for {character}")
                )

    def test_dice_rolling(self):
        """Test dice rolling functionality"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("TESTING DICE ROLLING")
        self.stdout.write("="*50)

        # Test various dice notations
        test_cases = [
            "1d20",
            "3d6",
            "1d8+3",
            "2d6-1",
        ]

        for notation in test_cases:
            try:
                result = DiceRollerService.parse_dice_notation(notation)
                self.stdout.write(
                    f"{notation}: {result.individual_rolls} = {result.total}"
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"{notation}: {str(e)}")
                )

        # Test ability score rolling
        self.stdout.write("\nAbility Score Rolling (4d6 drop lowest):")
        ability_rolls = DiceRollerService.roll_standard_ability_scores()
        for ability, roll_result in ability_rolls.items():
            self.stdout.write(
                f"  {ability}: {roll_result.individual_rolls} = {roll_result.total}"
            )

        # Test advantage/disadvantage
        self.stdout.write("\nAdvantage/Disadvantage:")
        advantage = DiceRollerService.roll_with_advantage(advantage_type='advantage')
        disadvantage = DiceRollerService.roll_with_advantage(advantage_type='disadvantage')

        self.stdout.write(
            f"  Advantage: [{advantage.roll1}, {advantage.roll2}] → {advantage.result}"
        )
        self.stdout.write(
            f"  Disadvantage: [{disadvantage.roll1}, {disadvantage.roll2}] → {disadvantage.result}"
        )