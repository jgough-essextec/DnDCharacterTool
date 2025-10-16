"""
Django management command to import D&D equipment from JSON files.

Usage:
    python manage.py import_equipment
    python manage.py import_equipment --data-dir /path/to/data
    python manage.py import_equipment --clear
"""

import json
from decimal import Decimal
from .base_importer import BaseImporter
from game_content.models import Equipment, Weapon, Armor


class Command(BaseImporter):
    help = 'Import D&D 5e equipment from items.json and items-base.json files'

    # Type mapping from JSON to our model choices
    TYPE_MAP = {
        # Weapons
        'M': 'weapon',     # Melee weapon
        'R': 'weapon',     # Ranged weapon
        # Armor
        'LA': 'armor',     # Light Armor
        'MA': 'armor',     # Medium Armor
        'HA': 'armor',     # Heavy Armor
        'S': 'shield',     # Shield
        # Other equipment
        'A': 'gear',       # Ammunition
        'G': 'gear',       # Adventuring gear
        'SCF': 'gear',     # Spellcasting focus
        'AT': 'tool',      # Artisan's tools
        'T': 'tool',       # Tools
        'GS': 'tool',      # Gaming set
        'INS': 'instrument', # Musical instrument
        'MNT': 'mount',    # Mount
        'TAH': 'gear',     # Tack and harness
        'TG': 'trade_good', # Trade goods
        'P': 'gear',       # Potion
        'SC': 'gear',      # Scroll
        'W': 'gear',       # Wondrous item
        'OTH': 'gear',     # Other
        '$': 'trade_good', # Currency/treasure
    }

    # Weapon properties to extract
    WEAPON_PROPERTIES = [
        'F',    # Finesse
        'H',    # Heavy
        'L',    # Light
        'LD',   # Loading
        'R',    # Reach
        'S',    # Special
        'T',    # Thrown
        '2H',   # Two-Handed
        'V',    # Versatile
        'AF',   # Ammunition (firearms)
        'A',    # Ammunition
        'RLD',  # Reload
    ]

    # Property descriptions
    PROPERTY_DESCRIPTIONS = {
        'F': 'Finesse',
        'H': 'Heavy',
        'L': 'Light',
        'LD': 'Loading',
        'R': 'Reach',
        'S': 'Special',
        'T': 'Thrown',
        '2H': 'Two-Handed',
        'V': 'Versatile',
        'AF': 'Ammunition',
        'A': 'Ammunition',
        'RLD': 'Reload',
    }

    def clear_existing_data(self):
        """Clear existing equipment data."""
        # Delete in reverse order due to inheritance
        if Weapon.objects.exists():
            count = Weapon.objects.count()
            Weapon.objects.all().delete()
            self.log(f"Deleted {count} existing weapons", style=self.style.WARNING)

        if Armor.objects.exists():
            count = Armor.objects.count()
            Armor.objects.all().delete()
            self.log(f"Deleted {count} existing armor", style=self.style.WARNING)

        if Equipment.objects.exists():
            count = Equipment.objects.count()
            Equipment.objects.all().delete()
            self.log(f"Deleted {count} existing equipment", style=self.style.WARNING)

    def import_data(self):
        """Import equipment from JSON files."""
        self.log("Starting equipment import...", style=self.style.SUCCESS)

        # Import from items-base.json first (base equipment)
        self.import_base_items()

        # Then import from items.json (magic items and variants)
        self.import_items()

    def import_base_items(self):
        """Import base equipment from items-base.json."""
        self.log("Importing base items...", level=1)

        data = self.load_json_file('items-base.json')
        if not data:
            return

        base_items = data.get('baseitem', [])
        if not base_items:
            self.log("No base items found in items-base.json", style=self.style.WARNING)
            return

        for item_data in base_items:
            try:
                if not self.is_valid_entry(item_data):
                    self.skipped_count += 1
                    self.log(f"Skipping {item_data.get('name', 'Unknown')} from {item_data.get('source', 'Unknown')}", level=2)
                    continue

                if self.validate_entry(item_data):
                    transformed = self.transform_entry(item_data)
                    if transformed:
                        self.save_entry(transformed)
                else:
                    self.skipped_count += 1
                    self.log(f"Validation failed for {item_data.get('name', 'Unknown')}", level=2, style=self.style.WARNING)

            except Exception as e:
                self.errors.append(f"Error processing item {item_data.get('name', 'Unknown')}: {str(e)}")
                self.log(f"Error processing item: {str(e)}", level=1, style=self.style.ERROR)
                if self.verbosity >= 3:
                    import traceback
                    traceback.print_exc()

    def import_items(self):
        """Import items from items.json."""
        self.log("Importing regular items...", level=1)

        data = self.load_json_file('items.json')
        if not data:
            return

        items = data.get('item', [])
        if not items:
            self.log("No items found in items.json", style=self.style.WARNING)
            return

        # Only import non-magical base equipment from items.json
        for item_data in items:
            try:
                # Skip magic items for now (rarity other than 'none')
                if item_data.get('rarity', 'none') != 'none':
                    self.skipped_count += 1
                    self.log(f"Skipping magic item: {item_data.get('name', 'Unknown')}", level=3)
                    continue

                if not self.is_valid_entry(item_data):
                    self.skipped_count += 1
                    self.log(f"Skipping {item_data.get('name', 'Unknown')} from {item_data.get('source', 'Unknown')}", level=2)
                    continue

                if self.validate_entry(item_data):
                    transformed = self.transform_entry(item_data)
                    if transformed:
                        self.save_entry(transformed)
                else:
                    self.skipped_count += 1
                    self.log(f"Validation failed for {item_data.get('name', 'Unknown')}", level=2, style=self.style.WARNING)

            except Exception as e:
                self.errors.append(f"Error processing item {item_data.get('name', 'Unknown')}: {str(e)}")
                self.log(f"Error processing item: {str(e)}", level=1, style=self.style.ERROR)
                if self.verbosity >= 3:
                    import traceback
                    traceback.print_exc()

    def validate_entry(self, entry):
        """Validate an equipment entry."""
        # Check required fields
        if not entry.get('name'):
            self.errors.append("Equipment entry missing name")
            return False

        # Check if we can determine the type
        item_type = entry.get('type')
        if item_type and item_type not in self.TYPE_MAP:
            self.log(f"Unknown item type '{item_type}' for {entry.get('name')}", level=2, style=self.style.WARNING)

        return True

    def extract_cost_in_gp(self, item_data):
        """Convert item value to gold pieces."""
        value = item_data.get('value')
        if not value:
            return Decimal('0.00')

        # If value is already in copper pieces (integer), convert to gold
        if isinstance(value, int):
            return Decimal(value) / 100

        # Handle other formats if needed
        return Decimal('0.00')

    def extract_weight(self, item_data):
        """Extract weight in pounds."""
        weight = item_data.get('weight', 0)
        return Decimal(str(weight))

    def extract_properties(self, item_data):
        """Extract item properties as a list."""
        properties = []
        item_props = item_data.get('property', [])

        for prop in item_props:
            # Properties might have source indicators like "AF|DMG"
            prop_code = prop.split('|')[0] if '|' in prop else prop
            if prop_code in self.PROPERTY_DESCRIPTIONS:
                properties.append(self.PROPERTY_DESCRIPTIONS[prop_code])

        return properties

    def determine_equipment_type(self, item_data):
        """Determine equipment type from JSON type."""
        item_type = item_data.get('type', 'OTH')
        return self.TYPE_MAP.get(item_type, 'gear')

    def extract_damage_info(self, item_data):
        """Extract damage dice and type for weapons."""
        damage_dice = item_data.get('dmg1', '')
        damage_type_code = item_data.get('dmgType', 'B')

        # Map damage type codes to our choices
        damage_type_map = {
            'A': 'acid',
            'B': 'bludgeoning',
            'C': 'cold',
            'E': 'lightning',
            'F': 'fire',
            'N': 'necrotic',
            'O': 'force',
            'P': 'piercing',
            'I': 'poison',
            'Y': 'psychic',
            'R': 'radiant',
            'S': 'slashing',
            'T': 'thunder',
        }

        damage_type = damage_type_map.get(damage_type_code, 'bludgeoning')

        return damage_dice, damage_type

    def extract_range(self, item_data):
        """Extract range for ranged weapons."""
        range_str = item_data.get('range')
        if not range_str:
            return None, None

        # Range format is "normal/long", e.g., "30/120"
        try:
            parts = range_str.split('/')
            if len(parts) == 2:
                return int(parts[0]), int(parts[1])
        except:
            pass

        return None, None

    def extract_armor_info(self, item_data):
        """Extract armor-specific information."""
        # Determine armor type from item type
        item_type = item_data.get('type')
        armor_type_map = {
            'LA': 'light',
            'MA': 'medium',
            'HA': 'heavy',
            'S': 'shield',
        }
        armor_type = armor_type_map.get(item_type, 'light')

        # Extract AC - may be in 'ac' field or need to be determined
        base_ac = item_data.get('ac', 10)
        if armor_type == 'shield':
            base_ac = 2  # Shields add +2 AC

        # Determine DEX bonus limit based on armor type
        dex_bonus_limit = None
        if armor_type == 'medium':
            dex_bonus_limit = 2
        elif armor_type == 'heavy':
            dex_bonus_limit = 0
        # Light armor and shields have no DEX limit (None)

        # Extract strength requirement
        strength_req = item_data.get('strength')

        # Check for stealth disadvantage
        stealth_disadvantage = item_data.get('stealth', False)

        return armor_type, base_ac, dex_bonus_limit, strength_req, stealth_disadvantage

    def transform_entry(self, entry):
        """Transform an equipment entry from JSON to Django model format."""
        # Extract common fields
        name = entry['name']
        equipment_type = self.determine_equipment_type(entry)
        cost_gp = self.extract_cost_in_gp(entry)
        weight = self.extract_weight(entry)
        properties = self.extract_properties(entry)

        # Extract description from entries
        description = ""
        if 'entries' in entry:
            description = self.parse_entries(entry['entries'])
        elif 'text' in entry:
            description = self.clean_text(entry['text'])

        # Base data for all equipment
        base_data = {
            'name': name,
            'equipment_type': equipment_type,
            'cost_gp': cost_gp,
            'weight': weight,
            'description': description,
            'properties': properties,
        }

        # Check if this is a weapon
        if equipment_type == 'weapon' and entry.get('weapon'):
            damage_dice, damage_type = self.extract_damage_info(entry)
            range_normal, range_long = self.extract_range(entry)
            weapon_category = 'martial' if entry.get('weaponCategory') == 'martial' else 'simple'

            return {
                'type': 'weapon',
                'base_data': base_data,
                'weapon_data': {
                    'weapon_category': weapon_category,
                    'damage_dice': damage_dice,
                    'damage_type': damage_type,
                    'range_normal': range_normal,
                    'range_long': range_long,
                    'mastery_property': entry.get('mastery', ''),
                }
            }

        # Check if this is armor
        elif equipment_type in ['armor', 'shield']:
            armor_type, base_ac, dex_bonus_limit, strength_req, stealth_disadvantage = self.extract_armor_info(entry)

            return {
                'type': 'armor',
                'base_data': base_data,
                'armor_data': {
                    'armor_type': armor_type,
                    'base_ac': base_ac,
                    'dex_bonus_limit': dex_bonus_limit,
                    'strength_requirement': strength_req,
                    'stealth_disadvantage': stealth_disadvantage,
                }
            }

        # Regular equipment
        else:
            return {
                'type': 'equipment',
                'base_data': base_data,
            }

    def save_entry(self, transformed_data):
        """Save or update an equipment entry."""
        try:
            item_type = transformed_data['type']
            base_data = transformed_data['base_data']

            if item_type == 'weapon':
                # Combine base and weapon-specific data
                weapon_data = {**base_data, **transformed_data['weapon_data']}

                weapon, created = Weapon.objects.update_or_create(
                    name=weapon_data['name'],
                    defaults=weapon_data
                )

                if created:
                    self.created_count += 1
                    self.log(f"Created weapon: {weapon.name}", level=2, style=self.style.SUCCESS)
                else:
                    self.updated_count += 1
                    self.log(f"Updated weapon: {weapon.name}", level=2)

            elif item_type == 'armor':
                # Combine base and armor-specific data
                armor_data = {**base_data, **transformed_data['armor_data']}

                armor, created = Armor.objects.update_or_create(
                    name=armor_data['name'],
                    defaults=armor_data
                )

                if created:
                    self.created_count += 1
                    self.log(f"Created armor: {armor.name}", level=2, style=self.style.SUCCESS)
                else:
                    self.updated_count += 1
                    self.log(f"Updated armor: {armor.name}", level=2)

            else:
                # Regular equipment
                equipment, created = Equipment.objects.update_or_create(
                    name=base_data['name'],
                    defaults=base_data
                )

                if created:
                    self.created_count += 1
                    self.log(f"Created equipment: {equipment.name}", level=2, style=self.style.SUCCESS)
                else:
                    self.updated_count += 1
                    self.log(f"Updated equipment: {equipment.name}", level=2)

        except Exception as e:
            self.errors.append(f"Failed to save equipment {base_data['name']}: {str(e)}")
            self.log(f"Failed to save equipment: {str(e)}", level=1, style=self.style.ERROR)