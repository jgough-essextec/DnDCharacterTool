"""
Django management command to import D&D classes from JSON files.

Usage:
    python manage.py import_classes
    python manage.py import_classes --data-dir /path/to/data
    python manage.py import_classes --clear
"""

import os
from pathlib import Path
from .base_importer import BaseImporter
from game_content.models import DnDClass, ClassFeature, Subclass


class Command(BaseImporter):
    help = 'Import D&D 5e classes from class/*.json files'

    def clear_existing_data(self):
        """Clear existing class data."""
        # Delete in reverse order due to foreign keys
        if Subclass.objects.exists():
            count = Subclass.objects.count()
            Subclass.objects.all().delete()
            self.log(f"Deleted {count} existing subclasses", style=self.style.WARNING)

        if ClassFeature.objects.exists():
            count = ClassFeature.objects.count()
            ClassFeature.objects.all().delete()
            self.log(f"Deleted {count} existing class features", style=self.style.WARNING)

        if DnDClass.objects.exists():
            count = DnDClass.objects.count()
            DnDClass.objects.all().delete()
            self.log(f"Deleted {count} existing classes", style=self.style.WARNING)

    def import_data(self):
        """Import classes from class/*.json files."""
        self.log("Starting class import...", style=self.style.SUCCESS)

        # Get all class JSON files from the class subdirectory
        class_dir = self.data_path / 'class'
        if not class_dir.exists():
            self.log(f"Class directory {class_dir} not found", level=1, style=self.style.ERROR)
            return

        # Process each class file
        for class_file in sorted(class_dir.glob('class-*.json')):
            self.log(f"Processing {class_file.name}...", level=2)

            # Load the JSON file
            try:
                with open(class_file, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                    self.log(f"Loaded {class_file.name}", level=2)
            except Exception as e:
                self.errors.append(f"Error loading {class_file.name}: {str(e)}")
                self.log(f"Error loading {class_file.name}: {str(e)}", level=1, style=self.style.ERROR)
                continue

            # Extract class array
            classes = data.get('class', [])
            if not classes:
                self.log(f"No classes found in {class_file.name}", style=self.style.WARNING)
                continue

            # Process each class
            for class_data in classes:
                try:
                    if not self.is_valid_entry(class_data):
                        self.skipped_count += 1
                        self.log(f"Skipping {class_data.get('name', 'Unknown')} from {class_data.get('source', 'Unknown')}", level=2)
                        continue

                    if self.validate_entry(class_data):
                        transformed = self.transform_entry(class_data)
                        if transformed:
                            self.save_entry(transformed)
                    else:
                        self.skipped_count += 1
                        self.log(f"Validation failed for {class_data.get('name', 'Unknown')}", level=2, style=self.style.WARNING)

                except Exception as e:
                    self.errors.append(f"Error processing class {class_data.get('name', 'Unknown')}: {str(e)}")
                    self.log(f"Error processing class: {str(e)}", level=1, style=self.style.ERROR)
                    if self.verbosity >= 3:
                        import traceback
                        traceback.print_exc()

    def validate_entry(self, entry):
        """Validate a class entry."""
        # Check required fields
        if not entry.get('name'):
            self.errors.append("Class entry missing name")
            return False

        return True

    def extract_primary_ability(self, class_data):
        """Extract primary ability for the class."""
        # Look for primary ability in various places
        if 'primaryAbility' in class_data:
            ability = class_data['primaryAbility']
            if isinstance(ability, dict):
                # Take first ability if multiple
                for key in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
                    if ability.get(key):
                        return key.upper()
            elif isinstance(ability, str):
                return ability.upper()

        # Fallback mappings based on class name
        ability_map = {
            'Barbarian': 'STR',
            'Bard': 'CHA',
            'Cleric': 'WIS',
            'Druid': 'WIS',
            'Fighter': 'STR',
            'Monk': 'WIS',
            'Paladin': 'STR',
            'Ranger': 'DEX',
            'Rogue': 'DEX',
            'Sorcerer': 'CHA',
            'Warlock': 'CHA',
            'Wizard': 'INT',
            'Artificer': 'INT'
        }

        return ability_map.get(class_data.get('name'), 'STR')

    def extract_hit_die(self, class_data):
        """Extract hit die size."""
        hd = class_data.get('hd', {})
        if isinstance(hd, dict):
            return hd.get('faces', 8)
        elif isinstance(hd, int):
            return hd
        return 8

    def extract_proficiencies(self, class_data):
        """Extract various proficiencies."""
        prof = class_data.get('proficiency', [])

        armor_profs = []
        weapon_profs = []
        save_profs = []

        if isinstance(prof, list):
            for p in prof:
                if isinstance(p, dict):
                    if p.get('armor'):
                        armor_profs.extend(p['armor'])
                    if p.get('weapons'):
                        weapon_profs.extend(p['weapons'])
                    if p.get('savingThrows'):
                        saves = p['savingThrows']
                        if isinstance(saves, list):
                            save_profs = [s.upper() if isinstance(s, str) else s for s in saves]
                elif isinstance(p, str):
                    # Try to categorize string proficiencies
                    p_lower = p.lower()
                    if any(armor in p_lower for armor in ['light', 'medium', 'heavy', 'shield']):
                        armor_profs.append(p)
                    elif any(weapon in p_lower for weapon in ['simple', 'martial', 'weapon']):
                        weapon_profs.append(p)

        return armor_profs, weapon_profs, save_profs

    def extract_skill_proficiencies(self, class_data):
        """Extract skill proficiency information."""
        # Skills are nested under startingProficiencies
        starting_prof = class_data.get('startingProficiencies', {})
        skills = starting_prof.get('skills', [])

        # Handle both array and dict formats
        if isinstance(skills, list) and skills:
            # Take the first element if it's an array
            skill_data = skills[0] if skills else {}
        else:
            skill_data = skills if isinstance(skills, dict) else {}

        if isinstance(skill_data, dict):
            count = skill_data.get('choose', {}).get('count', 2) if 'choose' in skill_data else 2
            choices = skill_data.get('choose', {}).get('from', []) if 'choose' in skill_data else []
            # Convert skill names to proper case (e.g., "acrobatics" -> "Acrobatics")
            choices = [skill.title().replace(' ', ' ') for skill in choices]
            return count, choices

        return 2, []

    def extract_features(self, class_data):
        """Extract class features by level."""
        features = []

        # Get features from classFeatures array
        class_features = class_data.get('classFeatures', [])

        for level in range(1, 21):  # Levels 1-20
            level_features = []

            # Find features for this level
            for feature_ref in class_features:
                if isinstance(feature_ref, str):
                    # Feature reference format: "Feature Name|PHB|1|optional"
                    parts = feature_ref.split('|')
                    if len(parts) >= 3:
                        feature_name = parts[0]
                        source = parts[1]
                        feature_level = parts[2]

                        # Check if this feature is for current level
                        if feature_level.isdigit() and int(feature_level) == level:
                            # Skip if not from valid source
                            if source not in self.VALID_SOURCES:
                                continue

                            level_features.append({
                                'name': feature_name,
                                'level': level,
                                'type': self.determine_feature_type(feature_name),
                                'description': f"{feature_name} gained at level {level}",
                                'choices': []
                            })

            features.extend(level_features)

        return features

    def determine_feature_type(self, feature_name):
        """Determine feature type based on name."""
        name_lower = feature_name.lower()

        if 'ability score' in name_lower:
            return 'asi'
        elif 'spellcasting' in name_lower:
            return 'spell'
        elif 'invocation' in name_lower:
            return 'invocation'
        elif 'maneuver' in name_lower or 'fighting style' in name_lower:
            return 'maneuver'
        else:
            return 'feature'

    def extract_subclasses(self, class_data):
        """Extract subclass information."""
        subclasses = []

        subclass_data = class_data.get('subclasses', [])
        for sub_ref in subclass_data:
            if isinstance(sub_ref, dict):
                # Direct subclass definition
                if sub_ref.get('source') in self.VALID_SOURCES:
                    subclasses.append({
                        'name': sub_ref.get('name', 'Unknown Subclass'),
                        'description': sub_ref.get('description', ''),
                        'level_available': sub_ref.get('level', 3)
                    })
            elif isinstance(sub_ref, str):
                # Subclass reference format: "Subclass Name|Source"
                parts = sub_ref.split('|')
                if len(parts) >= 2 and parts[1] in self.VALID_SOURCES:
                    subclasses.append({
                        'name': parts[0],
                        'description': f"A {parts[0]} specialization",
                        'level_available': 3  # Default for most classes
                    })

        return subclasses

    def determine_difficulty(self, class_name):
        """Determine class difficulty based on complexity."""
        easy = ['Barbarian', 'Fighter', 'Ranger', 'Rogue']
        hard = ['Artificer', 'Druid', 'Wizard', 'Warlock']

        if class_name in easy:
            return 'easy'
        elif class_name in hard:
            return 'hard'
        else:
            return 'moderate'

    def transform_entry(self, entry):
        """Transform a class entry from JSON to Django model format."""
        # Extract description
        description = ""
        if 'entries' in entry:
            for e in entry['entries']:
                if isinstance(e, str):
                    description = self.clean_text(e)
                    break
                elif isinstance(e, dict) and e.get('type') == 'section':
                    entries = e.get('entries', [])
                    if entries and isinstance(entries[0], str):
                        description = self.clean_text(entries[0])
                        break

        if not description:
            description = f"Masters of {entry['name']} arts."

        armor_profs, weapon_profs, save_profs = self.extract_proficiencies(entry)
        skill_count, skill_choices = self.extract_skill_proficiencies(entry)

        return {
            'name': entry['name'],
            'description': description,
            'primary_ability': self.extract_primary_ability(entry),
            'hit_die': self.extract_hit_die(entry),
            'difficulty': self.determine_difficulty(entry['name']),
            'armor_proficiencies': armor_profs,
            'weapon_proficiencies': weapon_profs,
            'saving_throw_proficiencies': save_profs,
            'skill_proficiency_count': skill_count,
            'skill_proficiency_choices': skill_choices,
            'features': self.extract_features(entry),
            'subclasses': self.extract_subclasses(entry)
        }

    def save_entry(self, transformed_data):
        """Save or update a class entry."""
        try:
            # Extract features and subclasses before saving class
            features = transformed_data.pop('features', [])
            subclasses = transformed_data.pop('subclasses', [])

            dnd_class, created = DnDClass.objects.update_or_create(
                name=transformed_data['name'],
                defaults=transformed_data
            )

            if created:
                self.created_count += 1
                self.log(f"Created class: {dnd_class.name}", level=2, style=self.style.SUCCESS)
            else:
                self.updated_count += 1
                self.log(f"Updated class: {dnd_class.name}", level=2)

            # Handle features
            if features:
                # Clear existing features if updating
                if not created:
                    dnd_class.features.all().delete()

                # Add new features
                for feature_data in features:
                    ClassFeature.objects.create(
                        dnd_class=dnd_class,
                        name=feature_data['name'],
                        level_acquired=feature_data['level'],
                        description=feature_data['description'],
                        feature_type=feature_data['type'],
                        choice_options=feature_data.get('choices', [])
                    )
                    self.log(f"  Added feature: {feature_data['name']} (Level {feature_data['level']})", level=3)

            # Handle subclasses
            if subclasses:
                # Clear existing subclasses if updating
                if not created:
                    dnd_class.subclasses.all().delete()

                # Add new subclasses
                for subclass_data in subclasses:
                    Subclass.objects.create(
                        dnd_class=dnd_class,
                        name=subclass_data['name'],
                        description=subclass_data['description'],
                        level_available=subclass_data['level_available']
                    )
                    self.log(f"  Added subclass: {subclass_data['name']}", level=3)

        except Exception as e:
            self.errors.append(f"Failed to save class {transformed_data['name']}: {str(e)}")
            self.log(f"Failed to save class: {str(e)}", level=1, style=self.style.ERROR)