"""
Django management command to import D&D data from JSON files.
"""

import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from game_content.models import (
    DnDClass, Background, Species, Feat, Spell, Equipment, Skill, Language
)


class Command(BaseCommand):
    help = 'Import D&D 5e data from JSON files into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default='data_script/dnd_data',
            help='Directory containing the JSON data files'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear all existing data before importing'
        )

    def handle(self, *args, **options):
        data_dir = Path(options['data_dir'])

        if not data_dir.exists():
            raise CommandError(f"Data directory {data_dir} does not exist")

        if options['clear_existing']:
            self.clear_existing_data()

        self.import_all_data(data_dir)

    def clear_existing_data(self):
        """Clear all existing game content data."""
        self.stdout.write("Clearing existing data...")

        # Delete in reverse dependency order
        Equipment.objects.all().delete()
        Spell.objects.all().delete()
        Feat.objects.all().delete()
        Species.objects.all().delete()
        Background.objects.all().delete()
        DnDClass.objects.all().delete()
        Skill.objects.all().delete()
        Language.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Existing data cleared"))

    def import_all_data(self, data_dir):
        """Import all data from JSON files."""
        importers = [
            ('languages.json', self.import_languages),
            ('skills.json', self.import_skills),
            ('classes.json', self.import_classes),
            ('backgrounds.json', self.import_backgrounds),
            ('races.json', self.import_species),  # Note: races.json -> Species model
            ('feats.json', self.import_feats),
            ('spells.json', self.import_spells),
            ('equipment.json', self.import_equipment),
        ]

        for filename, importer_func in importers:
            file_path = data_dir / filename
            if file_path.exists():
                self.stdout.write(f"Importing {filename}...")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if data:  # Only import if data is not empty
                        importer_func(data)
                        self.stdout.write(
                            self.style.SUCCESS(f"Successfully imported {len(data)} items from {filename}")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"No data found in {filename}")
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error importing {filename}: {e}")
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f"File {filename} not found, skipping...")
                )

    @transaction.atomic
    def import_languages(self, languages_data):
        """Import languages data."""
        for lang_data in languages_data:
            script = lang_data.get('script') or 'Common'  # Default to 'Common' if null/empty

            Language.objects.get_or_create(
                name=lang_data['name'],
                defaults={
                    'script': script,
                    'typical_speakers': ', '.join(lang_data.get('typical_speakers', [])) if isinstance(lang_data.get('typical_speakers'), list) else lang_data.get('typical_speakers', ''),
                    'rarity': lang_data.get('type', 'standard')
                }
            )

    @transaction.atomic
    def import_skills(self, skills_data):
        """Import skills data."""
        for skill_data in skills_data:
            Skill.objects.get_or_create(
                name=skill_data['name'],
                defaults={
                    'associated_ability': skill_data['ability'].upper(),
                    'description': skill_data['description']
                }
            )

    @transaction.atomic
    def import_classes(self, classes_data):
        """Import class data."""
        for class_data in classes_data:
            # Convert skill proficiency format
            skill_prof = class_data.get('skill_proficiencies', {})
            if isinstance(skill_prof, dict):
                skill_prof_formatted = {
                    'count': skill_prof.get('choose_count', 0),
                    'choices': skill_prof.get('available_skills', [])
                }
            else:
                skill_prof_formatted = {'count': 0, 'choices': []}

            DnDClass.objects.get_or_create(
                name=class_data['name'],
                defaults={
                    'description': class_data.get('description', ''),
                    'hit_die': class_data.get('hit_die', 8),
                    'primary_ability': class_data.get('primary_ability', '').upper(),
                    'difficulty': 'easy',  # Default difficulty
                    'armor_proficiencies': class_data.get('armor_proficiencies', []),
                    'weapon_proficiencies': class_data.get('weapon_proficiencies', []),
                    'saving_throw_proficiencies': [s.upper() for s in class_data.get('saving_throws', [])],
                    'skill_proficiency_count': skill_prof_formatted['count'],
                    'skill_proficiency_choices': skill_prof_formatted['choices']
                }
            )

    @transaction.atomic
    def import_backgrounds(self, backgrounds_data):
        """Import background data."""
        for bg_data in backgrounds_data:
            Background.objects.get_or_create(
                name=bg_data['name'],
                defaults={
                    'description': bg_data.get('description', ''),
                    'skill_proficiencies': bg_data.get('skill_proficiencies', []),
                    'tool_proficiencies': bg_data.get('tool_proficiencies', []),
                    'languages': bg_data.get('language_proficiencies', []),
                    'equipment_options': bg_data.get('starting_equipment', []),
                    'starting_gold': 15  # Default starting gold
                }
            )

    @transaction.atomic
    def import_species(self, species_data):
        """Import species/races data."""
        for species_info in species_data:
            size_mapping = {
                'Medium': 'M',
                'Small': 'S',
                'Large': 'L'
            }

            size_list = species_info.get('size', ['Medium'])
            size = size_list[0] if isinstance(size_list, list) else size_list
            size_code = size_mapping.get(size, 'M')

            Species.objects.get_or_create(
                name=species_info['name'],
                defaults={
                    'description': species_info.get('description', ''),
                    'size': size_code,
                    'speed': species_info.get('speed', {}).get('walk', 30),
                    'darkvision_range': species_info.get('darkvision', 0),
                    'languages': species_info.get('languages', [])
                }
            )

    @transaction.atomic
    def import_feats(self, feats_data):
        """Import feats data."""
        for feat_data in feats_data:
            feat_type = feat_data.get('category', 'general')
            if feat_type not in ['origin', 'general', 'fighting_style']:
                feat_type = 'general'

            # Handle prerequisites
            prereqs = feat_data.get('prerequisites', [])
            if isinstance(prereqs, dict):
                prereqs = [f"{k}: {v}" for k, v in prereqs.items()]

            Feat.objects.get_or_create(
                name=feat_data['name'],
                defaults={
                    'feat_type': feat_type,
                    'description': feat_data.get('description', ''),
                    'repeatable': feat_data.get('repeatable', False),
                    'prerequisites': prereqs,
                    'ability_score_increase': feat_data.get('ability_score_increase', []),
                    'benefits': [feat_data.get('description', '')]
                }
            )

    @transaction.atomic
    def import_spells(self, spells_data):
        """Import spells data."""
        for spell_data in spells_data:
            # Parse casting time
            casting_time_info = spell_data.get('casting_time', [{}])
            if casting_time_info and isinstance(casting_time_info, list):
                casting_time_data = casting_time_info[0]
                casting_time = f"{casting_time_data.get('number', 1)} {casting_time_data.get('unit', 'action')}"
            else:
                casting_time = "1 action"

            # Parse range
            range_info = spell_data.get('range', {})
            if isinstance(range_info, dict):
                if range_info.get('type') == 'point':
                    distance = range_info.get('distance', {})
                    range_value = f"{distance.get('amount', 0)} {distance.get('type', 'feet')}"
                elif range_info.get('type') == 'touch':
                    range_value = "touch"
                elif range_info.get('type') == 'self':
                    range_value = "self"
                else:
                    range_value = "30_feet"
            else:
                range_value = "30_feet"

            # Parse duration
            duration_info = spell_data.get('duration', [{}])
            if duration_info and isinstance(duration_info, list):
                duration_data = duration_info[0]
                if duration_data.get('type') == 'instant':
                    duration = "instantaneous"
                elif duration_data.get('type') == 'timed':
                    duration_time = duration_data.get('duration', {})
                    amount = duration_time.get('amount', 1)
                    unit = duration_time.get('type', 'minute')
                    duration = f"{amount}_{unit}"
                else:
                    duration = "instantaneous"
            else:
                duration = "instantaneous"

            # Components
            components = spell_data.get('components', {})
            components_v = components.get('v', False)
            components_s = components.get('s', False)
            components_m = components.get('m', False)
            if isinstance(components_m, str):
                material_components = components_m
                components_m = True
            else:
                material_components = ''

            spell, created = Spell.objects.get_or_create(
                name=spell_data['name'],
                defaults={
                    'spell_level': spell_data.get('level', 0),
                    'school': spell_data.get('school', 'evocation').lower(),
                    'casting_time': casting_time.lower(),
                    'range': range_value.lower(),
                    'duration': duration.lower(),
                    'components_v': components_v,
                    'components_s': components_s,
                    'components_m': components_m,
                    'material_components': material_components,
                    'concentration': spell_data.get('concentration', False),
                    'ritual': spell_data.get('ritual', False),
                    'description': '\n'.join(spell_data.get('description', [])),
                    'higher_level_description': '\n'.join(spell_data.get('higher_levels', []))
                }
            )

            # Add class associations
            if created:
                class_names = spell_data.get('classes', [])
                for class_name in class_names:
                    try:
                        dnd_class = DnDClass.objects.get(name=class_name)
                        spell.available_to_classes.add(dnd_class)
                    except DnDClass.DoesNotExist:
                        pass

    @transaction.atomic
    def import_equipment(self, equipment_data):
        """Import equipment data."""
        for item_data in equipment_data:
            # Parse value (convert from copper pieces to gold pieces if needed)
            value = item_data.get('value', 0)
            if isinstance(value, int):
                cost_gp = value / 100  # Assuming value is in copper pieces
            else:
                cost_gp = 0

            # Determine equipment type based on item data
            if item_data.get('weapon_category'):
                equipment_type = 'weapon'
            elif item_data.get('armor_type'):
                equipment_type = 'armor'
            else:
                equipment_type = 'general'

            Equipment.objects.get_or_create(
                name=item_data['name'],
                defaults={
                    'equipment_type': equipment_type,
                    'cost_gp': cost_gp,
                    'weight': item_data.get('weight', 0),
                    'description': '\n'.join(item_data.get('description', [])),
                    'properties': item_data.get('properties', [])
                }
            )