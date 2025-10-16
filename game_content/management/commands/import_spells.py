"""
Django management command to import D&D spells from JSON files.

Usage:
    python manage.py import_spells
    python manage.py import_spells --data-dir /path/to/data
    python manage.py import_spells --clear
"""

import os
from pathlib import Path
from .base_importer import BaseImporter
from game_content.models import Spell, DnDClass


class Command(BaseImporter):
    help = 'Import D&D 5e spells from spells/*.json files'

    def clear_existing_data(self):
        """Clear existing spell data."""
        if Spell.objects.exists():
            count = Spell.objects.count()
            Spell.objects.all().delete()
            self.log(f"Deleted {count} existing spells", style=self.style.WARNING)

    def import_data(self):
        """Import spells from spells/*.json files."""
        self.log("Starting spell import...", style=self.style.SUCCESS)

        # Get all spell JSON files from the spells subdirectory
        spells_dir = self.data_path / 'spells'
        if not spells_dir.exists():
            self.log(f"Spells directory {spells_dir} not found", level=1, style=self.style.ERROR)
            return

        # Process each spell file
        for spell_file in sorted(spells_dir.glob('spells-*.json')):
            # Skip fluff files
            if 'fluff' in spell_file.name:
                self.log(f"Skipping fluff file: {spell_file.name}", level=2)
                continue

            self.log(f"Processing {spell_file.name}...", level=2)

            # Load the JSON file
            try:
                with open(spell_file, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                    self.log(f"Loaded {spell_file.name}", level=2)
            except Exception as e:
                self.errors.append(f"Error loading {spell_file.name}: {str(e)}")
                self.log(f"Error loading {spell_file.name}: {str(e)}", level=1, style=self.style.ERROR)
                continue

            # Extract spell array
            spells = data.get('spell', [])
            if not spells:
                self.log(f"No spells found in {spell_file.name}", style=self.style.WARNING)
                continue

            # Process each spell
            for spell_data in spells:
                try:
                    if not self.is_valid_entry(spell_data):
                        self.skipped_count += 1
                        self.log(f"Skipping {spell_data.get('name', 'Unknown')} from {spell_data.get('source', 'Unknown')}", level=2)
                        continue

                    if self.validate_entry(spell_data):
                        transformed = self.transform_entry(spell_data)
                        if transformed:
                            self.save_entry(transformed)
                    else:
                        self.skipped_count += 1
                        self.log(f"Validation failed for {spell_data.get('name', 'Unknown')}", level=2, style=self.style.WARNING)

                except Exception as e:
                    self.errors.append(f"Error processing spell {spell_data.get('name', 'Unknown')}: {str(e)}")
                    self.log(f"Error processing spell: {str(e)}", level=1, style=self.style.ERROR)
                    if self.verbosity >= 3:
                        import traceback
                        traceback.print_exc()

    def validate_entry(self, entry):
        """Validate a spell entry."""
        # Check required fields
        if not entry.get('name'):
            self.errors.append("Spell entry missing name")
            return False

        if 'level' not in entry:
            self.errors.append(f"Spell {entry.get('name')} missing level")
            return False

        return True

    def extract_school(self, spell_data):
        """Extract spell school from short code."""
        school_map = {
            'A': 'abjuration',
            'C': 'conjuration',
            'D': 'divination',
            'E': 'enchantment',
            'V': 'evocation',
            'I': 'illusion',
            'N': 'necromancy',
            'T': 'transmutation'
        }
        return school_map.get(spell_data.get('school', 'V'), 'evocation')

    def extract_casting_time(self, spell_data):
        """Extract casting time from time array."""
        time_data = spell_data.get('time', [])
        if not time_data:
            return 'action'

        time_entry = time_data[0] if isinstance(time_data, list) else time_data

        if isinstance(time_entry, dict):
            number = time_entry.get('number', 1)
            unit = time_entry.get('unit', 'action')

            # Map to our choices
            if unit == 'action':
                return 'action'
            elif unit == 'bonus':
                return 'bonus_action'
            elif unit == 'reaction':
                return 'reaction'
            elif unit == 'minute':
                if number == 1:
                    return '1_minute'
                elif number == 10:
                    return '10_minutes'
            elif unit == 'hour':
                if number == 1:
                    return '1_hour'
                elif number == 8:
                    return '8_hours'
                elif number == 24:
                    return '24_hours'

        return 'action'  # Default

    def extract_range(self, spell_data):
        """Extract spell range."""
        range_data = spell_data.get('range', {})

        if isinstance(range_data, dict):
            range_type = range_data.get('type', '')

            if range_type == 'point':
                distance = range_data.get('distance', {})
                if isinstance(distance, dict):
                    amount = distance.get('amount', 0)
                    unit = distance.get('type', '')

                    # Map to our choices
                    if unit == 'feet':
                        if amount == 5:
                            return '5_feet'
                        elif amount == 10:
                            return '10_feet'
                        elif amount == 30:
                            return '30_feet'
                        elif amount == 60:
                            return '60_feet'
                        elif amount == 90:
                            return '90_feet'
                        elif amount == 120:
                            return '120_feet'
                        elif amount == 150:
                            return '150_feet'
                        elif amount == 300:
                            return '300_feet'
                        elif amount == 500:
                            return '500_feet'
                    elif unit == 'miles':
                        if amount == 1:
                            return '1_mile'
                    elif unit == 'sight':
                        return 'sight'
                elif distance == 'self':
                    return 'self'
                elif distance == 'touch':
                    return 'touch'
                elif distance == 'unlimited':
                    return 'unlimited'
            elif range_type == 'self':
                return 'self'
            elif range_type in ['touch', 'sight', 'unlimited']:
                return range_type

        return 'special'  # Default for complex ranges

    def extract_duration(self, spell_data):
        """Extract spell duration."""
        duration_data = spell_data.get('duration', [])
        if not duration_data:
            return 'instantaneous'

        duration_entry = duration_data[0] if isinstance(duration_data, list) else duration_data

        if isinstance(duration_entry, dict):
            duration_type = duration_entry.get('type', '')

            if duration_type == 'instant':
                return 'instantaneous'
            elif duration_type == 'timed':
                duration_info = duration_entry.get('duration', {})
                if isinstance(duration_info, dict):
                    amount = duration_info.get('amount', 0)
                    unit = duration_info.get('type', '')

                    # Map to our choices
                    if unit == 'round':
                        return '1_round'
                    elif unit == 'minute':
                        if amount == 1:
                            return '1_minute'
                        elif amount == 10:
                            return '10_minutes'
                    elif unit == 'hour':
                        if amount == 1:
                            return '1_hour'
                        elif amount == 8:
                            return '8_hours'
                        elif amount == 24:
                            return '24_hours'
                    elif unit == 'day':
                        if amount == 7:
                            return '7_days'
                        elif amount == 30:
                            return '30_days'
            elif duration_type == 'permanent':
                return 'permanent'
            elif duration_type == 'special':
                return 'special'

        return 'instantaneous'  # Default

    def extract_components(self, spell_data):
        """Extract spell components."""
        components = spell_data.get('components', {})

        v = components.get('v', False) if isinstance(components, dict) else False
        s = components.get('s', False) if isinstance(components, dict) else False

        # Material components can be boolean, string, or complex object
        m_data = components.get('m', False) if isinstance(components, dict) else False
        m = False
        material_text = ""

        if m_data:
            m = True  # Has material component
            if isinstance(m_data, str):
                material_text = m_data
            elif isinstance(m_data, dict):
                # Complex material component with cost and consume info
                text = m_data.get('text', '')
                cost = m_data.get('cost', 0)
                consume = m_data.get('consume', False)

                if cost > 0:
                    # Convert from copper to gold
                    gp_cost = cost / 100
                    material_text = f"{text} (worth {gp_cost:.0f} gp"
                    if consume:
                        material_text += ", consumed)"
                    else:
                        material_text += ")"
                else:
                    material_text = text
                    if consume:
                        material_text += " (consumed)"
            else:
                material_text = "Material components required"

        return v, s, m, material_text

    def extract_description(self, spell_data):
        """Extract spell description from entries."""
        description_parts = []

        entries = spell_data.get('entries', [])
        for entry in entries:
            if isinstance(entry, str):
                description_parts.append(self.clean_text(entry))
            elif isinstance(entry, dict):
                # Complex entry types
                if entry.get('type') == 'list':
                    items = entry.get('items', [])
                    for item in items:
                        if isinstance(item, str):
                            description_parts.append(f"• {self.clean_text(item)}")

        # Higher level description
        higher_level_parts = []
        higher_entries = spell_data.get('entriesHigherLevel', [])
        for entry in higher_entries:
            if isinstance(entry, dict) and entry.get('type') == 'entries':
                for sub_entry in entry.get('entries', []):
                    if isinstance(sub_entry, str):
                        higher_level_parts.append(self.clean_text(sub_entry))

        description = '\n\n'.join(description_parts)
        higher_level = '\n'.join(higher_level_parts)

        return description, higher_level

    def is_concentration(self, spell_data):
        """Check if spell requires concentration."""
        duration_data = spell_data.get('duration', [])
        if duration_data and isinstance(duration_data, list):
            duration_entry = duration_data[0]
            if isinstance(duration_entry, dict):
                return duration_entry.get('concentration', False)
        return False

    def is_ritual(self, spell_data):
        """Check if spell can be cast as a ritual."""
        meta = spell_data.get('meta', {})
        if isinstance(meta, dict):
            return meta.get('ritual', False)
        return False

    def transform_entry(self, entry):
        """Transform a spell entry from JSON to Django model format."""
        description, higher_level = self.extract_description(entry)
        v, s, m, material_text = self.extract_components(entry)

        return {
            'name': entry['name'],
            'spell_level': entry.get('level', 0),
            'school': self.extract_school(entry),
            'casting_time': self.extract_casting_time(entry),
            'range': self.extract_range(entry),
            'duration': self.extract_duration(entry),
            'concentration': self.is_concentration(entry),
            'ritual': self.is_ritual(entry),
            'components_v': v,
            'components_s': s,
            'components_m': m,
            'material_components': material_text,
            'description': description,
            'higher_level_description': higher_level,
        }

    def save_entry(self, transformed_data):
        """Save or update a spell entry."""
        try:
            spell, created = Spell.objects.update_or_create(
                name=transformed_data['name'],
                defaults=transformed_data
            )

            if created:
                self.created_count += 1
                self.log(f"Created spell: {spell.name}", level=2, style=self.style.SUCCESS)
            else:
                self.updated_count += 1
                self.log(f"Updated spell: {spell.name}", level=2)

        except Exception as e:
            self.errors.append(f"Error saving spell {transformed_data['name']}: {str(e)}")
            self.log(f"Error saving spell: {str(e)}", level=1, style=self.style.ERROR)