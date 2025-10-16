"""
Django management command to import D&D backgrounds from JSON files.

Usage:
    python manage.py import_backgrounds
    python manage.py import_backgrounds --data-dir /path/to/data
    python manage.py import_backgrounds --clear
"""

from .base_importer import BaseImporter
from game_content.models import Background


class Command(BaseImporter):
    help = 'Import D&D 5e backgrounds from backgrounds.json'

    def clear_existing_data(self):
        """Clear existing backgrounds data."""
        if Background.objects.exists():
            count = Background.objects.count()
            Background.objects.all().delete()
            self.log(f"Deleted {count} existing backgrounds", style=self.style.WARNING)

    def import_data(self):
        """Import backgrounds from backgrounds.json."""
        self.log("Starting backgrounds import...", style=self.style.SUCCESS)

        # Load the JSON file
        data = self.load_json_file('backgrounds.json')
        if not data:
            return

        # Extract background array
        backgrounds = data.get('background', [])
        if not backgrounds:
            self.log("No backgrounds found in data file", style=self.style.WARNING)
            return

        # Process each background
        for bg_data in backgrounds:
            try:
                if not self.is_valid_entry(bg_data):
                    self.skipped_count += 1
                    self.log(f"Skipping {bg_data.get('name', 'Unknown')} from {bg_data.get('source', 'Unknown')}", level=2)
                    continue

                if self.validate_entry(bg_data):
                    transformed = self.transform_entry(bg_data)
                    if transformed:
                        self.save_entry(transformed)
                else:
                    self.skipped_count += 1
                    self.log(f"Validation failed for {bg_data.get('name', 'Unknown')}", level=2, style=self.style.WARNING)

            except Exception as e:
                self.errors.append(f"Error processing background {bg_data.get('name', 'Unknown')}: {str(e)}")
                self.log(f"Error processing background: {str(e)}", level=1, style=self.style.ERROR)
                if self.verbosity >= 3:
                    import traceback
                    traceback.print_exc()

    def validate_entry(self, entry):
        """Validate a background entry."""
        # Check required fields
        if not entry.get('name'):
            self.errors.append("Background entry missing name")
            return False

        return True

    def extract_skill_proficiencies(self, bg_data):
        """Extract skill proficiencies from background data."""
        skills = []

        skill_profs = bg_data.get('skillProficiencies', [])
        if isinstance(skill_profs, list):
            for skill in skill_profs:
                if isinstance(skill, dict):
                    # Handle different skill formats
                    if 'any' in skill:
                        skills.append("Any " + str(skill['any']) + " skills")
                    elif 'choose' in skill:
                        choose_data = skill['choose']
                        if isinstance(choose_data, dict):
                            from_skills = choose_data.get('from', [])
                            count = choose_data.get('count', 1)
                            if from_skills:
                                skills.append(f"Choose {count} from: {', '.join(from_skills)}")
                    else:
                        # Direct skill names
                        for skill_name in ['athletics', 'acrobatics', 'sleight of hand', 'stealth',
                                         'arcana', 'history', 'investigation', 'nature', 'religion',
                                         'animal handling', 'insight', 'medicine', 'perception', 'survival',
                                         'deception', 'intimidation', 'performance', 'persuasion']:
                            if skill.get(skill_name):
                                skills.append(skill_name.title())
                elif isinstance(skill, str):
                    skills.append(skill)

        return skills

    def extract_tool_proficiencies(self, bg_data):
        """Extract tool proficiencies from background data."""
        tools = []

        tool_profs = bg_data.get('toolProficiencies', [])
        if isinstance(tool_profs, list):
            for tool in tool_profs:
                if isinstance(tool, dict):
                    # Handle different tool formats
                    if 'any' in tool:
                        tools.append("Any " + str(tool['any']) + " tools")
                    elif 'choose' in tool:
                        choose_data = tool['choose']
                        if isinstance(choose_data, dict):
                            from_tools = choose_data.get('from', [])
                            count = choose_data.get('count', 1)
                            if from_tools:
                                tools.append(f"Choose {count} from: {', '.join(from_tools)}")
                    else:
                        # Direct tool names
                        tool_names = []
                        for key, value in tool.items():
                            if value and key not in ['choose', 'any']:
                                tool_names.append(key.replace('_', ' ').title())
                        tools.extend(tool_names)
                elif isinstance(tool, str):
                    tools.append(tool)

        return tools

    def extract_languages(self, bg_data):
        """Extract language proficiencies from background data."""
        languages = []

        lang_profs = bg_data.get('languageProficiencies', [])
        if isinstance(lang_profs, list):
            for lang in lang_profs:
                if isinstance(lang, dict):
                    # Handle different language formats
                    if 'any' in lang:
                        count = lang['any']
                        languages.append(f"Any {count} language{'s' if count > 1 else ''}")
                    elif 'anyStandard' in lang:
                        count = lang['anyStandard']
                        languages.append(f"Any {count} standard language{'s' if count > 1 else ''}")
                    elif 'choose' in lang:
                        choose_data = lang['choose']
                        if isinstance(choose_data, dict):
                            from_langs = choose_data.get('from', [])
                            count = choose_data.get('count', 1)
                            if from_langs:
                                languages.append(f"Choose {count} from: {', '.join(from_langs)}")
                    else:
                        # Direct language names
                        for key, value in lang.items():
                            if value and key not in ['choose', 'any', 'anyStandard']:
                                languages.append(key.title())
                elif isinstance(lang, str):
                    languages.append(lang)

        return languages

    def extract_equipment(self, bg_data):
        """Extract starting equipment from background data."""
        equipment = []

        start_equip = bg_data.get('startingEquipment', [])
        if isinstance(start_equip, list):
            for item in start_equip:
                if isinstance(item, dict):
                    # Handle item entries
                    item_name = item.get('item', '')
                    quantity = item.get('quantity', 1)
                    if item_name:
                        if quantity > 1:
                            equipment.append(f"{item_name} ({quantity})")
                        else:
                            equipment.append(item_name)
                elif isinstance(item, str):
                    equipment.append(item)

        # Also check entries for equipment lists
        if 'entries' in bg_data:
            for entry in bg_data['entries']:
                if isinstance(entry, dict) and entry.get('name') == 'Equipment':
                    equip_entries = entry.get('entries', [])
                    for equip_entry in equip_entries:
                        if isinstance(equip_entry, str):
                            # Parse equipment from text
                            equipment.append(self.clean_text(equip_entry))

        return equipment

    def extract_starting_gold(self, bg_data):
        """Extract starting gold amount."""
        # Look for starting gold in various places
        if 'startingGold' in bg_data:
            return bg_data['startingGold']

        # Check entries for gold information
        if 'entries' in bg_data:
            for entry in bg_data['entries']:
                if isinstance(entry, dict) and 'gold' in str(entry).lower():
                    # Try to extract number from text
                    import re
                    match = re.search(r'(\d+)\s*(?:gp|gold)', str(entry), re.IGNORECASE)
                    if match:
                        return int(match.group(1))

        # Default starting gold
        return 15

    def transform_entry(self, entry):
        """Transform a background entry from JSON to Django model format."""
        # Extract description
        description = ""
        if 'entries' in entry:
            for e in entry['entries']:
                if isinstance(e, str):
                    description = self.clean_text(e)
                    break
                elif isinstance(e, dict) and e.get('type') == 'entries' and not e.get('name'):
                    desc_entries = e.get('entries', [])
                    if desc_entries and isinstance(desc_entries[0], str):
                        description = self.clean_text(desc_entries[0])
                        break

        if not description:
            description = f"Those with the {entry['name']} background."

        return {
            'name': entry['name'],
            'description': description,
            'skill_proficiencies': self.extract_skill_proficiencies(entry),
            'tool_proficiencies': self.extract_tool_proficiencies(entry),
            'languages': self.extract_languages(entry),
            'equipment_options': self.extract_equipment(entry),
            'starting_gold': self.extract_starting_gold(entry),
            # Origin feat will be linked later when we import feats
            'origin_feat': None
        }

    def save_entry(self, transformed_data):
        """Save or update a background entry."""
        try:
            background, created = Background.objects.update_or_create(
                name=transformed_data['name'],
                defaults=transformed_data
            )

            if created:
                self.created_count += 1
                self.log(f"Created background: {background.name}", level=2, style=self.style.SUCCESS)
            else:
                self.updated_count += 1
                self.log(f"Updated background: {background.name}", level=2)

            # Log details at higher verbosity
            if self.verbosity >= 3:
                self.log(f"  Skills: {', '.join(background.skill_proficiencies) if background.skill_proficiencies else 'None'}", level=3)
                self.log(f"  Tools: {', '.join(background.tool_proficiencies) if background.tool_proficiencies else 'None'}", level=3)
                self.log(f"  Languages: {', '.join(background.languages) if background.languages else 'None'}", level=3)

        except Exception as e:
            self.errors.append(f"Failed to save background {transformed_data['name']}: {str(e)}")
            self.log(f"Failed to save background: {str(e)}", level=1, style=self.style.ERROR)