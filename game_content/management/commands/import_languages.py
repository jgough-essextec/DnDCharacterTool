"""
Django management command to import D&D languages from JSON files.

Usage:
    python manage.py import_languages
    python manage.py import_languages --data-dir /path/to/data
    python manage.py import_languages --clear
"""

import re
from .base_importer import BaseImporter
from game_content.models import Language


class Command(BaseImporter):
    help = 'Import D&D 5e languages from languages.json'

    def clear_existing_data(self):
        """Clear existing languages data."""
        if Language.objects.exists():
            count = Language.objects.count()
            Language.objects.all().delete()
            self.log(f"Deleted {count} existing languages", style=self.style.WARNING)

    def import_data(self):
        """Import languages from languages.json."""
        self.log("Starting languages import...", style=self.style.SUCCESS)

        # Load the JSON file
        data = self.load_json_file('languages.json')
        if not data:
            return

        # Extract language array
        languages = data.get('language', [])
        if not languages:
            self.log("No languages found in data file", style=self.style.WARNING)
            return

        # Process each language
        for lang_data in languages:
            try:
                if not self.is_valid_entry(lang_data):
                    self.skipped_count += 1
                    self.log(f"Skipping {lang_data.get('name', 'Unknown')} from {lang_data.get('source', 'Unknown')}", level=2)
                    continue

                if self.validate_entry(lang_data):
                    transformed = self.transform_entry(lang_data)
                    if transformed:
                        self.save_entry(transformed)
                else:
                    self.skipped_count += 1
                    self.log(f"Validation failed for {lang_data.get('name', 'Unknown')}", level=2, style=self.style.WARNING)

            except Exception as e:
                self.errors.append(f"Error processing language {lang_data.get('name', 'Unknown')}: {str(e)}")
                self.log(f"Error processing language: {str(e)}", level=1, style=self.style.ERROR)
                if self.verbosity >= 3:
                    import traceback
                    traceback.print_exc()

    def validate_entry(self, entry):
        """Validate a language entry."""
        # Check required fields
        if not entry.get('name'):
            self.errors.append("Language entry missing name")
            return False

        return True

    def clean_typical_speakers(self, speakers):
        """Clean and format typical speakers list."""
        if not speakers:
            return ""

        cleaned_speakers = []

        if isinstance(speakers, list):
            for speaker in speakers:
                if isinstance(speaker, str):
                    # Remove tags like {@creature ...} and extract the readable part
                    cleaned = self.clean_text(speaker)
                    if cleaned:
                        cleaned_speakers.append(cleaned)
        elif isinstance(speakers, str):
            cleaned = self.clean_text(speakers)
            if cleaned:
                cleaned_speakers.append(cleaned)

        # Join with commas and return
        return ", ".join(cleaned_speakers)

    def determine_rarity(self, entry):
        """Determine language rarity based on type field or infer from name."""
        # Check explicit type field
        lang_type = entry.get('type', '').lower()
        if lang_type in ['standard', 'exotic', 'secret', 'rare']:
            if lang_type in ['secret', 'rare']:
                return 'exotic'  # Map secret/rare to exotic
            return lang_type

        # If no type, infer from common exotic languages
        exotic_languages = [
            'Abyssal', 'Celestial', 'Deep Speech', 'Draconic', 'Infernal',
            'Primordial', 'Sylvan', 'Undercommon', 'Druidic', 'Thieves\' Cant',
            'Qualith', 'Gith', 'Slaad', 'Sphinx'
        ]

        if entry.get('name') in exotic_languages:
            return 'exotic'

        # Default to standard
        return 'standard'

    def determine_script(self, entry):
        """Determine the script for a language."""
        # Use explicit script if provided
        script = entry.get('script', '')
        if script:
            return script

        # Common script mappings based on D&D conventions
        script_mappings = {
            'Common': 'Common',
            'Dwarvish': 'Dwarvish',
            'Elvish': 'Elvish',
            'Giant': 'Dwarvish',
            'Gnomish': 'Dwarvish',
            'Goblin': 'Dwarvish',
            'Halfling': 'Common',
            'Orc': 'Dwarvish',
            'Abyssal': 'Infernal',
            'Celestial': 'Celestial',
            'Draconic': 'Draconic',
            'Deep Speech': '',  # No script
            'Infernal': 'Infernal',
            'Primordial': 'Dwarvish',
            'Sylvan': 'Elvish',
            'Undercommon': 'Elvish',
            'Druidic': '',  # Special - typically not written
            'Thieves\' Cant': '',  # Special - uses existing languages
        }

        # Try to find script based on language name
        lang_name = entry.get('name', '')
        return script_mappings.get(lang_name, 'Common')

    def transform_entry(self, entry):
        """Transform a language entry from JSON to Django model format."""
        # Clean up typical speakers
        speakers = self.clean_typical_speakers(entry.get('typicalSpeakers', []))

        # Determine rarity
        rarity = self.determine_rarity(entry)

        # Determine script
        script = self.determine_script(entry)

        return {
            'name': entry['name'],
            'script': script,
            'typical_speakers': speakers,
            'rarity': rarity
        }

    def save_entry(self, transformed_data):
        """Save or update a language entry."""
        try:
            language, created = Language.objects.update_or_create(
                name=transformed_data['name'],
                defaults={
                    'script': transformed_data['script'],
                    'typical_speakers': transformed_data['typical_speakers'],
                    'rarity': transformed_data['rarity']
                }
            )

            if created:
                self.created_count += 1
                self.log(f"Created language: {language.name} ({language.rarity})", level=2, style=self.style.SUCCESS)
            else:
                self.updated_count += 1
                self.log(f"Updated language: {language.name} ({language.rarity})", level=2)

        except Exception as e:
            self.errors.append(f"Failed to save language {transformed_data['name']}: {str(e)}")
            self.log(f"Failed to save language: {str(e)}", level=1, style=self.style.ERROR)