"""
Django management command to import D&D 2024 game data.

Usage:
    python manage.py import_dnd_data
    python manage.py import_dnd_data --flush  # Clear existing data first
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from game_content.models import (
    Skill, Language, Feat, Species, SpeciesTrait,
    DnDClass, ClassFeature, Subclass, Background,
    Equipment, Weapon, Armor, Spell
)


class Command(BaseCommand):
    help = 'Import D&D 2024 game content data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete existing game content before importing',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write(
                self.style.WARNING('Flushing existing game content...')
            )
            self.flush_existing_data()

        try:
            with transaction.atomic():
                self.stdout.write('Importing D&D 2024 game content...')

                # Import in dependency order
                self.import_skills()
                self.import_languages()
                self.import_feats()
                self.import_species()
                self.import_classes()
                self.import_backgrounds()
                self.import_equipment()
                self.import_spells()

                self.stdout.write(
                    self.style.SUCCESS('Successfully imported D&D game content!')
                )

        except Exception as e:
            raise CommandError(f'Import failed: {str(e)}')

    def flush_existing_data(self):
        """Remove all existing game content"""
        models_to_flush = [
            Spell, Armor, Weapon, Equipment, Background,
            Subclass, ClassFeature, DnDClass, SpeciesTrait,
            Species, Feat, Language, Skill
        ]

        for model in models_to_flush:
            count = model.objects.count()
            if count > 0:
                model.objects.all().delete()
                self.stdout.write(f'Deleted {count} {model._meta.verbose_name_plural}')

    def import_skills(self):
        """Import the 18 core D&D skills"""
        skills_data = [
            ('Acrobatics', 'DEX', 'Balance, diving, rolling, tumbling, and flipping.'),
            ('Animal Handling', 'WIS', 'Calming, controlling, or understanding animals.'),
            ('Arcana', 'INT', 'Knowledge of magic, magical items, and spells.'),
            ('Athletics', 'STR', 'Climbing, jumping, swimming, and physical activities.'),
            ('Deception', 'CHA', 'Lying, misleading, and concealing information.'),
            ('History', 'INT', 'Knowledge of historical events, people, and cultures.'),
            ('Insight', 'WIS', 'Reading body language and understanding motivations.'),
            ('Intimidation', 'CHA', 'Frightening or coercing others through threats.'),
            ('Investigation', 'INT', 'Finding clues, analyzing evidence, and deduction.'),
            ('Medicine', 'WIS', 'Treating injuries, diseases, and medical conditions.'),
            ('Nature', 'INT', 'Knowledge of plants, animals, weather, and terrain.'),
            ('Perception', 'WIS', 'Noticing details and being aware of surroundings.'),
            ('Performance', 'CHA', 'Entertaining others through music, dance, or acting.'),
            ('Persuasion', 'CHA', 'Convincing others through honest argument.'),
            ('Religion', 'INT', 'Knowledge of gods, religious practices, and divine magic.'),
            ('Sleight of Hand', 'DEX', 'Manual dexterity for pickpocketing and trickery.'),
            ('Stealth', 'DEX', 'Hiding, moving silently, and avoiding detection.'),
            ('Survival', 'WIS', 'Tracking, navigation, and surviving in the wilderness.'),
        ]

        for name, ability, description in skills_data:
            skill, created = Skill.objects.get_or_create(
                name=name,
                defaults={
                    'associated_ability': ability,
                    'description': description
                }
            )
            if created:
                self.stdout.write(f'Created skill: {name}')

        self.stdout.write(f'Skills: {Skill.objects.count()} total')

    def import_languages(self):
        """Import D&D languages"""
        languages_data = [
            # Standard Languages
            ('Common', 'Common', 'Humans, most civilized races', 'standard'),
            ('Dwarvish', 'Dwarvish', 'Dwarves', 'standard'),
            ('Elvish', 'Elvish', 'Elves', 'standard'),
            ('Giant', 'Dwarvish', 'Giants, ogres', 'standard'),
            ('Gnomish', 'Dwarvish', 'Gnomes', 'standard'),
            ('Goblin', 'Dwarvish', 'Goblins, hobgoblins, bugbears', 'standard'),
            ('Halfling', 'Common', 'Halflings', 'standard'),
            ('Orc', 'Dwarvish', 'Orcs', 'standard'),

            # Exotic Languages
            ('Abyssal', 'Infernal', 'Demons, chaotic evil outsiders', 'exotic'),
            ('Celestial', 'Celestial', 'Angels, good outsiders', 'exotic'),
            ('Draconic', 'Draconic', 'Dragons, dragonborn, kobolds', 'exotic'),
            ('Deep Speech', '', 'Aberrations, mind flayers', 'exotic'),
            ('Infernal', 'Infernal', 'Devils, lawful evil outsiders', 'exotic'),
            ('Primordial', 'Dwarvish', 'Elementals, genies', 'exotic'),
            ('Sylvan', 'Elvish', 'Fey creatures, dryads', 'exotic'),
            ('Undercommon', 'Elvish', 'Underdark traders, dark elves', 'exotic'),
        ]

        for name, script, speakers, rarity in languages_data:
            language, created = Language.objects.get_or_create(
                name=name,
                defaults={
                    'script': script,
                    'typical_speakers': speakers,
                    'rarity': rarity
                }
            )
            if created:
                self.stdout.write(f'Created language: {name}')

        self.stdout.write(f'Languages: {Language.objects.count()} total')

    def import_feats(self):
        """Import sample D&D 2024 feats"""
        feats_data = [
            # Origin Feats
            {
                'name': 'Alert',
                'feat_type': 'origin',
                'description': 'Always on the lookout for danger, you gain the following benefits: Initiative bonus, can\'t be surprised while conscious.',
                'benefits': ['+5 bonus to initiative rolls', 'Cannot be surprised while conscious'],
                'repeatable': False
            },
            {
                'name': 'Crafter',
                'feat_type': 'origin',
                'description': 'You are adept at crafting things and bargaining with merchants.',
                'benefits': ['Tool proficiency', 'Crafting discount', 'Selling bonus'],
                'repeatable': False
            },
            {
                'name': 'Healer',
                'feat_type': 'origin',
                'description': 'You are an able physician, allowing you to mend wounds quickly.',
                'benefits': ['Medicine proficiency', 'Bonus healing with healer\'s kit'],
                'repeatable': False
            },

            # General Feats
            {
                'name': 'Ability Score Improvement',
                'feat_type': 'general',
                'description': 'Increase one ability score by 2, or two ability scores by 1 each.',
                'ability_score_increase': {'choice': 'any', 'points': 2},
                'repeatable': True
            },
            {
                'name': 'Grappler',
                'feat_type': 'general',
                'description': 'You\'ve developed the skills necessary to hold your own in close-quarters grappling.',
                'prerequisites': {'strength': 13},
                'benefits': ['Advantage on grapple attacks', 'Restrain grappled creatures'],
                'repeatable': False
            },

            # Fighting Style Feats
            {
                'name': 'Archery',
                'feat_type': 'fighting_style',
                'description': 'You gain a +2 bonus to attack rolls you make with ranged weapons.',
                'benefits': ['+2 to ranged attack rolls'],
                'repeatable': False
            },
            {
                'name': 'Defense',
                'feat_type': 'fighting_style',
                'description': 'While you are wearing armor, you gain a +1 bonus to AC.',
                'benefits': ['+1 AC while wearing armor'],
                'repeatable': False
            }
        ]

        for feat_data in feats_data:
            feat, created = Feat.objects.get_or_create(
                name=feat_data['name'],
                defaults=feat_data
            )
            if created:
                self.stdout.write(f'Created feat: {feat_data["name"]}')

        self.stdout.write(f'Feats: {Feat.objects.count()} total')

    def import_species(self):
        """Import D&D 2024 species"""
        species_data = [
            {
                'name': 'Human',
                'description': 'Humans are the most adaptable and ambitious people among the common species.',
                'size': 'M',
                'speed': 30,
                'darkvision_range': 0,
                'languages': ['Common'],
                'traits': [
                    ('Resourceful', 'racial', 'Gain Heroic Inspiration when you finish a Long Rest.'),
                    ('Skillful', 'racial', 'You gain proficiency in one skill of your choice.'),
                    ('Versatile', 'racial', 'You gain an Origin feat of your choice.')
                ]
            },
            {
                'name': 'Elf',
                'description': 'Elves are a magical people of otherworldly grace, living in places of ethereal beauty.',
                'size': 'M',
                'speed': 30,
                'darkvision_range': 60,
                'languages': ['Common', 'Elvish'],
                'traits': [
                    ('Elven Lineage', 'racial', 'You are part of a lineage that grants you supernatural abilities.'),
                    ('Fey Ancestry', 'racial', 'You have Advantage on saving throws you make to avoid or end the Charmed condition.'),
                    ('Keen Senses', 'proficiency', 'You have proficiency in the Perception skill.'),
                    ('Trance', 'racial', 'You don\'t need to sleep, and magic can\'t put you to sleep.')
                ]
            },
            {
                'name': 'Dwarf',
                'description': 'Bold and hardy, dwarves are known as skilled warriors, miners, and workers of stone and metal.',
                'size': 'M',
                'speed': 25,
                'darkvision_range': 60,
                'languages': ['Common', 'Dwarvish'],
                'traits': [
                    ('Dwarven Lineage', 'racial', 'You are part of a dwarven lineage that grants you supernatural abilities.'),
                    ('Dwarven Resilience', 'resistance', 'You have Resistance to Poison damage and Advantage on saving throws you make to avoid or end the Poisoned condition.'),
                    ('Dwarven Toughness', 'racial', 'Your Hit Point maximum increases by 1, and it increases by 1 again whenever you gain a level.'),
                    ('Stonecunning', 'racial', 'As a Bonus Action, you gain Tremorsense with a range of 60 feet for 10 minutes.')
                ]
            }
        ]

        for species_info in species_data:
            traits = species_info.pop('traits')
            species, created = Species.objects.get_or_create(
                name=species_info['name'],
                defaults=species_info
            )
            if created:
                self.stdout.write(f'Created species: {species_info["name"]}')

                # Add traits
                for trait_name, trait_type, description in traits:
                    SpeciesTrait.objects.create(
                        species=species,
                        name=trait_name,
                        trait_type=trait_type,
                        description=description
                    )

        self.stdout.write(f'Species: {Species.objects.count()} total')

    def import_classes(self):
        """Import sample D&D classes"""
        classes_data = [
            {
                'name': 'Fighter',
                'description': 'A master of martial combat, skilled with a variety of weapons and armor.',
                'primary_ability': 'STR',
                'hit_die': 10,
                'difficulty': 'easy',
                'armor_proficiencies': ['light', 'medium', 'heavy', 'shields'],
                'weapon_proficiencies': ['simple', 'martial'],
                'saving_throw_proficiencies': ['STR', 'CON'],
                'skill_proficiency_count': 2,
                'skill_proficiency_choices': ['Acrobatics', 'Animal Handling', 'Athletics', 'History', 'Insight', 'Intimidation', 'Perception', 'Survival'],
                'features': [
                    (1, 'Fighting Style', 'feature', 'Choose a fighting style specialty.', []),
                    (1, 'Second Wind', 'feature', 'Regain hit points as a bonus action.', []),
                    (2, 'Action Surge', 'feature', 'Take an additional action on your turn.', []),
                    (3, 'Martial Archetype', 'feature', 'Choose your fighter archetype.', []),
                    (4, 'Ability Score Improvement', 'asi', 'Increase ability scores or take a feat.', [])
                ]
            },
            {
                'name': 'Wizard',
                'description': 'A scholarly magic-user capable of manipulating the structures of reality.',
                'primary_ability': 'INT',
                'hit_die': 6,
                'difficulty': 'hard',
                'armor_proficiencies': [],
                'weapon_proficiencies': ['daggers', 'darts', 'slings', 'quarterstaffs', 'light crossbows'],
                'saving_throw_proficiencies': ['INT', 'WIS'],
                'skill_proficiency_count': 2,
                'skill_proficiency_choices': ['Arcana', 'History', 'Insight', 'Investigation', 'Medicine', 'Religion'],
                'features': [
                    (1, 'Spellcasting', 'spell', 'Cast wizard spells using Intelligence.', []),
                    (1, 'Arcane Recovery', 'feature', 'Recover spell slots on a short rest.', []),
                    (2, 'Arcane Tradition', 'feature', 'Choose your magical specialty.', []),
                    (4, 'Ability Score Improvement', 'asi', 'Increase ability scores or take a feat.', [])
                ]
            }
        ]

        for class_info in classes_data:
            features = class_info.pop('features')
            dnd_class, created = DnDClass.objects.get_or_create(
                name=class_info['name'],
                defaults=class_info
            )
            if created:
                self.stdout.write(f'Created class: {class_info["name"]}')

                # Add class features
                for level, name, feat_type, description, choices in features:
                    ClassFeature.objects.create(
                        dnd_class=dnd_class,
                        name=name,
                        level_acquired=level,
                        description=description,
                        feature_type=feat_type,
                        choice_options=choices
                    )

        self.stdout.write(f'Classes: {DnDClass.objects.count()} total')

    def import_backgrounds(self):
        """Import sample D&D backgrounds"""
        backgrounds_data = [
            {
                'name': 'Acolyte',
                'description': 'You have spent your life in service to a temple, learning sacred rites and providing sacrifices.',
                'skill_proficiencies': ['Insight', 'Religion'],
                'tool_proficiencies': [],
                'languages': ['Any two languages'],
                'equipment_options': ['Holy symbol', 'Prayer book', 'Incense'],
                'starting_gold': 15
            },
            {
                'name': 'Criminal',
                'description': 'You are an experienced criminal with a history of breaking the law.',
                'skill_proficiencies': ['Deception', 'Stealth'],
                'tool_proficiencies': ['Thieves\' tools', 'Gaming set'],
                'languages': [],
                'equipment_options': ['Crowbar', 'Dark common clothes', 'Belt pouch'],
                'starting_gold': 15
            },
            {
                'name': 'Folk Hero',
                'description': 'You come from humble social rank, but you are destined for much more.',
                'skill_proficiencies': ['Animal Handling', 'Survival'],
                'tool_proficiencies': ['Artisan tools', 'Vehicles (land)'],
                'languages': [],
                'equipment_options': ['Artisan tools', 'Shovel', 'Common clothes'],
                'starting_gold': 10
            }
        ]

        for bg_data in backgrounds_data:
            background, created = Background.objects.get_or_create(
                name=bg_data['name'],
                defaults=bg_data
            )
            if created:
                self.stdout.write(f'Created background: {bg_data["name"]}')

        self.stdout.write(f'Backgrounds: {Background.objects.count()} total')

    def import_equipment(self):
        """Import sample equipment"""
        # Simple Weapons
        weapons_data = [
            {
                'name': 'Dagger',
                'equipment_type': 'weapon',
                'weapon_category': 'simple',
                'damage_dice': '1d4',
                'damage_type': 'piercing',
                'cost_gp': 2.00,
                'weight': 1.0,
                'properties': ['finesse', 'light', 'thrown'],
                'range_normal': 20,
                'range_long': 60,
                'mastery_property': 'Nick'
            },
            {
                'name': 'Longsword',
                'equipment_type': 'weapon',
                'weapon_category': 'martial',
                'damage_dice': '1d8',
                'damage_type': 'slashing',
                'cost_gp': 15.00,
                'weight': 3.0,
                'properties': ['versatile'],
                'mastery_property': 'Sap'
            }
        ]

        for weapon_data in weapons_data:
            weapon, created = Weapon.objects.get_or_create(
                name=weapon_data['name'],
                defaults=weapon_data
            )
            if created:
                self.stdout.write(f'Created weapon: {weapon_data["name"]}')

        # Armor
        armor_data = [
            {
                'name': 'Leather Armor',
                'equipment_type': 'armor',
                'armor_type': 'light',
                'base_ac': 11,
                'dex_bonus_limit': None,
                'cost_gp': 10.00,
                'weight': 10.0,
                'stealth_disadvantage': False
            },
            {
                'name': 'Chain Mail',
                'equipment_type': 'armor',
                'armor_type': 'heavy',
                'base_ac': 16,
                'dex_bonus_limit': 0,
                'strength_requirement': 13,
                'cost_gp': 75.00,
                'weight': 55.0,
                'stealth_disadvantage': True
            }
        ]

        for armor_info in armor_data:
            armor, created = Armor.objects.get_or_create(
                name=armor_info['name'],
                defaults=armor_info
            )
            if created:
                self.stdout.write(f'Created armor: {armor_info["name"]}')

        self.stdout.write(f'Equipment: {Equipment.objects.count()} total')

    def import_spells(self):
        """Import sample spells"""
        spells_data = [
            {
                'name': 'Cantrip - Fire Bolt',
                'spell_level': 0,
                'school': 'evocation',
                'casting_time': 'action',
                'range': '120_feet',
                'duration': 'instantaneous',
                'concentration': False,
                'ritual': False,
                'components_v': True,
                'components_s': True,
                'components_m': False,
                'description': 'You hurl a mote of fire at a creature or object within range.',
                'classes': ['Wizard']
            },
            {
                'name': 'Magic Missile',
                'spell_level': 1,
                'school': 'evocation',
                'casting_time': 'action',
                'range': '120_feet',
                'duration': 'instantaneous',
                'concentration': False,
                'ritual': False,
                'components_v': True,
                'components_s': True,
                'components_m': False,
                'description': 'You create three glowing darts of magical force.',
                'higher_level_description': 'When you cast this spell using a spell slot of 2nd level or higher, the spell creates one more dart for each slot level above 1st.',
                'classes': ['Wizard']
            },
            {
                'name': 'Cure Wounds',
                'spell_level': 1,
                'school': 'evocation',
                'casting_time': 'action',
                'range': 'touch',
                'duration': 'instantaneous',
                'concentration': False,
                'ritual': False,
                'components_v': True,
                'components_s': True,
                'components_m': False,
                'description': 'A creature you touch regains a number of hit points.',
                'classes': []  # Will add to appropriate classes
            }
        ]

        for spell_data in spells_data:
            class_names = spell_data.pop('classes', [])
            spell, created = Spell.objects.get_or_create(
                name=spell_data['name'],
                defaults=spell_data
            )
            if created:
                self.stdout.write(f'Created spell: {spell_data["name"]}')

                # Add class availability
                for class_name in class_names:
                    try:
                        dnd_class = DnDClass.objects.get(name=class_name)
                        spell.available_to_classes.add(dnd_class)
                    except DnDClass.DoesNotExist:
                        pass

        self.stdout.write(f'Spells: {Spell.objects.count()} total')