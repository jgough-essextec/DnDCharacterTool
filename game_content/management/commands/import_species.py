"""
Django management command to import D&D species (races) from JSON files.

Usage:
    python manage.py import_species
    python manage.py import_species --data-dir /path/to/data
    python manage.py import_species --clear
"""

import re
from .base_importer import BaseImporter
from game_content.models import Species, SpeciesTrait


class Command(BaseImporter):
    help = 'Import D&D 5e species (races) from races.json'

    def clear_existing_data(self):
        """Clear existing species and traits data."""
        # Delete in reverse order due to foreign key
        if SpeciesTrait.objects.exists():
            count = SpeciesTrait.objects.count()
            SpeciesTrait.objects.all().delete()
            self.log(f"Deleted {count} existing species traits", style=self.style.WARNING)

        if Species.objects.exists():
            count = Species.objects.count()
            Species.objects.all().delete()
            self.log(f"Deleted {count} existing species", style=self.style.WARNING)

    def import_data(self):
        """Import species from races.json."""
        self.log("Starting species import...", style=self.style.SUCCESS)

        # Load the JSON file
        data = self.load_json_file('races.json')
        if not data:
            return

        # Extract race array
        races = data.get('race', [])
        if not races:
            self.log("No races found in data file", style=self.style.WARNING)
            return

        # Process each race
        for race_data in races:
            try:
                if not self.is_valid_entry(race_data):
                    self.skipped_count += 1
                    self.log(f"Skipping {race_data.get('name', 'Unknown')} from {race_data.get('source', 'Unknown')}", level=2)
                    continue

                if self.validate_entry(race_data):
                    transformed = self.transform_entry(race_data)
                    if transformed:
                        self.save_entry(transformed)
                else:
                    self.skipped_count += 1
                    self.log(f"Validation failed for {race_data.get('name', 'Unknown')}", level=2, style=self.style.WARNING)

            except Exception as e:
                self.errors.append(f"Error processing race {race_data.get('name', 'Unknown')}: {str(e)}")
                self.log(f"Error processing race: {str(e)}", level=1, style=self.style.ERROR)
                if self.verbosity >= 3:
                    import traceback
                    traceback.print_exc()

    def validate_entry(self, entry):
        """Validate a species entry."""
        # Check required fields
        if not entry.get('name'):
            self.errors.append("Species entry missing name")
            return False

        return True

    def extract_size(self, race_data):
        """Extract size from race data."""
        size_map = {
            'T': 'T', 'Tiny': 'T',
            'S': 'S', 'Small': 'S',
            'M': 'M', 'Medium': 'M',
            'L': 'L', 'Large': 'L',
            'H': 'H', 'Huge': 'H',
            'G': 'G', 'Gargantuan': 'G'
        }

        # Get size - can be string or array
        size_info = race_data.get('size', 'M')
        if isinstance(size_info, list) and size_info:
            size_info = size_info[0]

        return size_map.get(size_info, 'M')

    def extract_speed(self, race_data):
        """Extract base walking speed from race data."""
        speed_info = race_data.get('speed', 30)

        # Handle different speed formats
        if isinstance(speed_info, int):
            return speed_info
        elif isinstance(speed_info, dict):
            return speed_info.get('walk', 30)
        elif isinstance(speed_info, str):
            # Try to extract number from string
            match = re.search(r'\d+', speed_info)
            return int(match.group()) if match else 30

        return 30

    def extract_darkvision(self, race_data):
        """Extract darkvision range from race data."""
        darkvision = race_data.get('darkvision', 0)

        if isinstance(darkvision, int):
            return darkvision
        elif isinstance(darkvision, str):
            match = re.search(r'\d+', darkvision)
            return int(match.group()) if match else 0

        return 0

    def extract_languages(self, race_data):
        """Extract language proficiencies."""
        languages = []

        lang_profs = race_data.get('languageProficiencies', [])
        if isinstance(lang_profs, list):
            for lang in lang_profs:
                if isinstance(lang, dict):
                    # Extract language name from dict format
                    if lang.get('common'):
                        languages.append('Common')
                    elif lang.get('dwarvish'):
                        languages.append('Dwarvish')
                    elif lang.get('elvish'):
                        languages.append('Elvish')
                    elif lang.get('anyStandard'):
                        languages.append('Any standard language')
                    elif 'name' in lang:
                        languages.append(lang['name'])
                elif isinstance(lang, str):
                    languages.append(lang)

        return languages

    def extract_traits(self, race_data):
        """Extract racial traits from race data."""
        traits = []

        # Check different locations for traits
        trait_sources = [
            race_data.get('entries', []),
            race_data.get('racialTraits', []),
            race_data.get('traitTags', [])
        ]

        for source in trait_sources:
            if isinstance(source, list):
                for entry in source:
                    if isinstance(entry, dict):
                        name = entry.get('name', '')
                        if name and name not in ['Age', 'Size', 'Languages']:
                            # Parse the trait
                            description = self.parse_entries(entry.get('entries', []))
                            trait_type = self.determine_trait_type(name, description)

                            traits.append({
                                'name': name,
                                'description': description,
                                'trait_type': trait_type,
                                'mechanical_effect': {}  # Could parse mechanical effects later
                            })

        return traits

    def determine_trait_type(self, name, description):
        """Determine the type of trait based on name and description."""
        name_lower = name.lower()
        desc_lower = description.lower()

        if 'resistance' in name_lower or 'resistance' in desc_lower:
            return 'resistance'
        elif 'immunity' in name_lower or 'immunity' in desc_lower:
            return 'immunity'
        elif 'proficiency' in name_lower or 'proficiency' in desc_lower:
            return 'proficiency'
        elif any(ability in name_lower for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']):
            return 'ability'
        else:
            return 'racial'

    def transform_entry(self, entry):
        """Transform a species entry from JSON to Django model format."""
        # Extract description
        description = ""
        if 'entries' in entry:
            # Find the main description entry (usually first non-trait entry)
            for e in entry['entries']:
                if isinstance(e, str):
                    description = self.clean_text(e)
                    break
                elif isinstance(e, dict) and e.get('type') == 'entries' and not e.get('name'):
                    description = self.parse_entries(e.get('entries', []))
                    break

        if not description:
            description = f"A member of the {entry['name']} species."

        return {
            'name': entry['name'],
            'description': description,
            'size': self.extract_size(entry),
            'speed': self.extract_speed(entry),
            'darkvision_range': self.extract_darkvision(entry),
            'languages': self.extract_languages(entry),
            'traits': self.extract_traits(entry)
        }

    def save_entry(self, transformed_data):
        """Save or update a species entry."""
        try:
            # Extract traits before saving species
            traits = transformed_data.pop('traits', [])

            species, created = Species.objects.update_or_create(
                name=transformed_data['name'],
                defaults=transformed_data
            )

            if created:
                self.created_count += 1
                self.log(f"Created species: {species.name}", level=2, style=self.style.SUCCESS)
            else:
                self.updated_count += 1
                self.log(f"Updated species: {species.name}", level=2)

            # Handle traits
            if traits:
                # Clear existing traits if updating
                if not created:
                    species.traits.all().delete()

                # Add new traits
                for trait_data in traits:
                    SpeciesTrait.objects.create(
                        species=species,
                        name=trait_data['name'],
                        description=trait_data['description'],
                        trait_type=trait_data['trait_type'],
                        mechanical_effect=trait_data.get('mechanical_effect', {})
                    )
                    self.log(f"  Added trait: {trait_data['name']}", level=3)

        except Exception as e:
            self.errors.append(f"Failed to save species {transformed_data['name']}: {str(e)}")
            self.log(f"Failed to save species: {str(e)}", level=1, style=self.style.ERROR)