"""
Django management command to import D&D skills from JSON files.

Usage:
    python manage.py import_skills
    python manage.py import_skills --data-dir /path/to/data
    python manage.py import_skills --clear
"""

from .base_importer import BaseImporter
from game_content.models import Skill


class Command(BaseImporter):
    help = 'Import D&D 5e skills from skills.json'

    def clear_existing_data(self):
        """Clear existing skills data."""
        if Skill.objects.exists():
            count = Skill.objects.count()
            Skill.objects.all().delete()
            self.log(f"Deleted {count} existing skills", style=self.style.WARNING)

    def import_data(self):
        """Import skills from skills.json."""
        self.log("Starting skills import...", style=self.style.SUCCESS)

        # Load the JSON file
        data = self.load_json_file('skills.json')
        if not data:
            return

        # Extract skill array
        skills = data.get('skill', [])
        if not skills:
            self.log("No skills found in data file", style=self.style.WARNING)
            return

        # Process each skill
        for skill_data in skills:
            try:
                if not self.is_valid_entry(skill_data):
                    self.skipped_count += 1
                    self.log(f"Skipping {skill_data.get('name', 'Unknown')} from {skill_data.get('source', 'Unknown')}", level=2)
                    continue

                if self.validate_entry(skill_data):
                    transformed = self.transform_entry(skill_data)
                    if transformed:
                        self.save_entry(transformed)
                else:
                    self.skipped_count += 1
                    self.log(f"Validation failed for {skill_data.get('name', 'Unknown')}", level=2, style=self.style.WARNING)

            except Exception as e:
                self.errors.append(f"Error processing skill {skill_data.get('name', 'Unknown')}: {str(e)}")
                self.log(f"Error processing skill: {str(e)}", level=1, style=self.style.ERROR)
                if self.verbosity >= 3:
                    import traceback
                    traceback.print_exc()

    def validate_entry(self, entry):
        """Validate a skill entry."""
        # Check required fields
        if not entry.get('name'):
            self.errors.append("Skill entry missing name")
            return False

        if not entry.get('ability'):
            self.errors.append(f"Skill {entry['name']} missing ability")
            return False

        # Validate ability is a known value
        valid_abilities = ['str', 'dex', 'con', 'int', 'wis', 'cha']
        if entry['ability'].lower() not in valid_abilities:
            self.errors.append(f"Skill {entry['name']} has invalid ability: {entry['ability']}")
            return False

        return True

    def transform_entry(self, entry):
        """Transform a skill entry from JSON to Django model format."""
        # Convert ability to uppercase
        ability_map = {
            'str': 'STR',
            'dex': 'DEX',
            'con': 'CON',
            'int': 'INT',
            'wis': 'WIS',
            'cha': 'CHA'
        }

        ability = ability_map.get(entry['ability'].lower())
        if not ability:
            self.errors.append(f"Unable to map ability {entry['ability']} for skill {entry['name']}")
            return None

        # Parse description from entries
        description = ""
        if 'entries' in entry and entry['entries']:
            description = self.parse_entries(entry['entries'])

        # If no description from entries, create a basic one
        if not description:
            description = f"Make a {entry['name']} check."

        return {
            'name': entry['name'],
            'associated_ability': ability,
            'description': description
        }

    def save_entry(self, transformed_data):
        """Save or update a skill entry."""
        try:
            skill, created = Skill.objects.update_or_create(
                name=transformed_data['name'],
                defaults={
                    'associated_ability': transformed_data['associated_ability'],
                    'description': transformed_data['description']
                }
            )

            if created:
                self.created_count += 1
                self.log(f"Created skill: {skill.name}", level=2, style=self.style.SUCCESS)
            else:
                self.updated_count += 1
                self.log(f"Updated skill: {skill.name}", level=2)

        except Exception as e:
            self.errors.append(f"Failed to save skill {transformed_data['name']}: {str(e)}")
            self.log(f"Failed to save skill: {str(e)}", level=1, style=self.style.ERROR)