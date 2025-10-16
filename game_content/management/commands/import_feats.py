"""
Django management command to import D&D feats from JSON files.

Usage:
    python manage.py import_feats
    python manage.py import_feats --data-dir /path/to/data
    python manage.py import_feats --clear
"""

import re
from .base_importer import BaseImporter
from game_content.models import Feat


class Command(BaseImporter):
    help = 'Import D&D 5e feats from feats.json'

    def clear_existing_data(self):
        """Clear existing feats data."""
        if Feat.objects.exists():
            count = Feat.objects.count()
            Feat.objects.all().delete()
            self.log(f"Deleted {count} existing feats", style=self.style.WARNING)

    def import_data(self):
        """Import feats from feats.json."""
        self.log("Starting feats import...", style=self.style.SUCCESS)

        # Load the JSON file
        data = self.load_json_file('feats.json')
        if not data:
            return

        # Extract feat array
        feats = data.get('feat', [])
        if not feats:
            self.log("No feats found in data file", style=self.style.WARNING)
            return

        # Process each feat
        for feat_data in feats:
            try:
                if not self.is_valid_entry(feat_data):
                    self.skipped_count += 1
                    self.log(f"Skipping {feat_data.get('name', 'Unknown')} from {feat_data.get('source', 'Unknown')}", level=2)
                    continue

                if self.validate_entry(feat_data):
                    transformed = self.transform_entry(feat_data)
                    if transformed:
                        self.save_entry(transformed)
                else:
                    self.skipped_count += 1
                    self.log(f"Validation failed for {feat_data.get('name', 'Unknown')}", level=2, style=self.style.WARNING)

            except Exception as e:
                self.errors.append(f"Error processing feat {feat_data.get('name', 'Unknown')}: {str(e)}")
                self.log(f"Error processing feat: {str(e)}", level=1, style=self.style.ERROR)
                if self.verbosity >= 3:
                    import traceback
                    traceback.print_exc()

    def validate_entry(self, entry):
        """Validate a feat entry."""
        # Check required fields
        if not entry.get('name'):
            self.errors.append("Feat entry missing name")
            return False

        return True

    def determine_feat_type(self, feat_data):
        """Determine the type of feat."""
        name = feat_data.get('name', '').lower()

        # Check for fighting style feats
        if 'fighting style' in name or 'fighting initiate' in name:
            return 'fighting_style'

        # Check for specific fighting styles
        fighting_styles = ['archery', 'defense', 'dueling', 'great weapon fighting',
                         'protection', 'two-weapon fighting', 'blessed warrior',
                         'blind fighting', 'interception', 'thrown weapon fighting',
                         'unarmed fighting', 'close quarters shooter', 'mariner',
                         'tunnel fighter', 'druidic warrior']

        if any(style in name for style in fighting_styles):
            return 'fighting_style'

        # Check for origin feats (typically background feats)
        if feat_data.get('category') == 'background' or feat_data.get('category') == 'origin':
            return 'origin'

        # Check tags for origin feats
        feat_tags = feat_data.get('featureType', [])
        if isinstance(feat_tags, list) and 'BG' in feat_tags:
            return 'origin'

        # Default to general
        return 'general'

    def extract_prerequisites(self, feat_data):
        """Extract and format prerequisites."""
        prerequisites = {}

        # Check prerequisite field
        prereq = feat_data.get('prerequisite', [])
        if isinstance(prereq, list):
            for p in prereq:
                if isinstance(p, dict):
                    # Handle ability score requirements
                    if 'ability' in p:
                        for ability in p['ability']:
                            if isinstance(ability, dict):
                                for score, value in ability.items():
                                    if score in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
                                        prerequisites[score] = value

                    # Handle level requirements
                    if 'level' in p:
                        prerequisites['level'] = p['level']

                    # Handle proficiency requirements
                    if 'proficiency' in p:
                        prerequisites['proficiency'] = p['proficiency']

                    # Handle spellcasting requirements
                    if 'spellcasting' in p and p['spellcasting']:
                        prerequisites['spellcasting'] = True

                    # Handle other requirements
                    if 'other' in p:
                        prerequisites['other'] = p['other']

        return prerequisites

    def extract_ability_score_increase(self, feat_data):
        """Extract ability score increase information."""
        asi_info = {}

        # Check for ability score increases
        ability = feat_data.get('ability', [])
        if isinstance(ability, list):
            for a in ability:
                if isinstance(a, dict):
                    # Handle "choose" format
                    if 'choose' in a:
                        choose_data = a['choose']
                        if isinstance(choose_data, dict):
                            amount = choose_data.get('amount', 1)
                            count = choose_data.get('count', 1)
                            from_abilities = choose_data.get('from', [])
                            asi_info['choice'] = {
                                'amount': amount,
                                'count': count,
                                'from': from_abilities
                            }
                    else:
                        # Handle direct ability increases
                        for ability_name in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
                            if ability_name in a:
                                asi_info[ability_name] = a[ability_name]

        return asi_info

    def extract_benefits(self, feat_data):
        """Extract the benefits/features of the feat."""
        benefits = []

        # Get main entries
        if 'entries' in feat_data:
            entries = feat_data['entries']
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, str):
                        benefit = self.clean_text(entry)
                        if benefit and len(benefit) > 10:  # Skip very short entries
                            benefits.append(benefit)
                    elif isinstance(entry, dict):
                        # Handle list entries
                        if entry.get('type') == 'list':
                            items = entry.get('items', [])
                            for item in items:
                                if isinstance(item, str):
                                    benefits.append(self.clean_text(item))
                                elif isinstance(item, dict) and 'entry' in item:
                                    benefits.append(self.clean_text(item['entry']))
                        # Handle other entry types
                        elif 'entries' in entry:
                            sub_entries = self.parse_entries(entry['entries'])
                            if sub_entries:
                                benefits.append(sub_entries)

        # If no benefits found, create a basic one
        if not benefits:
            benefits = [f"Grants the benefits of the {feat_data.get('name', 'Unknown')} feat."]

        return benefits

    def transform_entry(self, entry):
        """Transform a feat entry from JSON to Django model format."""
        # Extract description
        description = ""
        if 'entries' in entry:
            # Get first non-list entry as description
            for e in entry['entries']:
                if isinstance(e, str):
                    description = self.clean_text(e)
                    break
                elif isinstance(e, dict) and e.get('type') != 'list':
                    desc_text = self.parse_entries([e])
                    if desc_text:
                        description = desc_text
                        break

        if not description:
            description = f"The {entry['name']} feat."

        return {
            'name': entry['name'],
            'feat_type': self.determine_feat_type(entry),
            'description': description,
            'repeatable': entry.get('repeatable', False),
            'prerequisites': self.extract_prerequisites(entry),
            'ability_score_increase': self.extract_ability_score_increase(entry),
            'benefits': self.extract_benefits(entry)
        }

    def save_entry(self, transformed_data):
        """Save or update a feat entry."""
        try:
            feat, created = Feat.objects.update_or_create(
                name=transformed_data['name'],
                defaults=transformed_data
            )

            if created:
                self.created_count += 1
                self.log(f"Created feat: {feat.name} ({feat.feat_type})", level=2, style=self.style.SUCCESS)
            else:
                self.updated_count += 1
                self.log(f"Updated feat: {feat.name} ({feat.feat_type})", level=2)

            # Log details at higher verbosity
            if self.verbosity >= 3:
                if feat.prerequisites:
                    self.log(f"  Prerequisites: {feat.prerequisites}", level=3)
                if feat.ability_score_increase:
                    self.log(f"  ASI: {feat.ability_score_increase}", level=3)
                if len(feat.benefits) > 0:
                    self.log(f"  Benefits: {len(feat.benefits)} entries", level=3)

        except Exception as e:
            self.errors.append(f"Failed to save feat {transformed_data['name']}: {str(e)}")
            self.log(f"Failed to save feat: {str(e)}", level=1, style=self.style.ERROR)