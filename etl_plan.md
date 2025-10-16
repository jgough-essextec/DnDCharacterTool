# D&D Character Creator - Detailed ETL Plan

## Overview

This document outlines the detailed Extract, Transform, Load (ETL) plan for importing D&D 5e data from JSON files into the Django database. The plan follows a phased approach to ensure data integrity and proper relationships.

## Data Source Structure

- **Location**: `/home/jdgough/DnDCharacterTool/data/`
- **Format**: JSON files from 5etools
- **Key Files**:
  - `skills.json` - Core skills data
  - `languages.json` - Language definitions
  - `feats.json` - Character feats
  - `races.json` - Species/race data
  - `backgrounds.json` - Character backgrounds
  - `class/*.json` - Individual class files
  - `spells/*.json` - Spell data by source book
  - `items.json` - Equipment data
  - `items-base.json` - Basic equipment

## Filtering Strategy

### Source Book Filtering
**Include**: PHB, XGE, TCE, SCAG, and all other official WotC 5e publications
**Exclude**: XPHB (2024 edition), UA (Unearthed Arcana), homebrew content

### Implementation
```python
VALID_SOURCES = [
    'PHB', 'XGE', 'TCE', 'SCAG', 'MM', 'VGM', 'MTF', 'GGR', 'AI', 'EGW',
    'MOT', 'IDRotF', 'TCoE', 'FTD', 'SCC', 'DSotDQ', 'BMT', 'BPG'
]

EXCLUDED_SOURCES = ['XPHB', 'UA', 'homebrew']

def is_valid_entry(entry):
    source = entry.get('source', '')
    return source in VALID_SOURCES and source not in EXCLUDED_SOURCES
```

## Phase 1: Core Reference Data

### 1.1 Skills Import

**Source**: `skills.json`
**Target Model**: `game_content.Skill`

#### Data Mapping
```
JSON Field          → Django Field
name                → name
ability             → associated_ability (convert to uppercase)
entries[0]          → description (join text if multiple entries)
```

#### Transformation Rules
1. Filter entries where `source` is not "XPHB"
2. Convert ability codes: "dex" → "DEX", "str" → "STR", etc.
3. For entries with complex structure in description, extract plain text
4. Handle duplicate names by keeping PHB version over other sources

#### Validation
- Ensure name is unique
- Validate ability is in ABILITY_CHOICES
- Description must not be empty

### 1.2 Languages Import

**Source**: `languages.json`
**Target Model**: `game_content.Language`

#### Data Mapping
```
JSON Field          → Django Field
name                → name
script              → script (default: "Common" if not present)
typicalSpeakers     → typical_speakers (join array as comma-separated string)
type                → rarity (standard/exotic, default: "standard")
```

#### Transformation Rules
1. Filter out XPHB entries
2. For `typicalSpeakers` array, strip tags like "{@creature ...}" and extract clean names
3. Map `type` values: "standard" → "standard", "exotic" → "exotic", others → "standard"
4. If script is missing, infer from similar languages or default to "Common"

#### Validation
- Name must be unique
- Rarity must be valid choice

## Phase 2: Character Options

### 2.1 Species (Races) Import

**Source**: `races.json`
**Target Model**: `game_content.Species` and `game_content.SpeciesTrait`

#### Data Mapping - Species
```
JSON Field          → Django Field
name                → name
entries             → description (combine text entries)
size                → size (map full names to codes: "Medium" → "M")
speed               → speed (extract base walking speed)
darkvision          → darkvision_range (default: 0)
languageProficiencies → languages (extract language names)
```

#### Data Mapping - Species Traits
```
JSON Field          → Django Field
(parent)            → species (FK)
name                → name (from trait entries)
entries             → description
type                → trait_type (infer from content)
(various)           → mechanical_effect (JSON)
```

#### Transformation Rules
1. Each subrace becomes its own Species entry (e.g., "High Elf" separate from "Elf")
2. Extract traits from various JSON structures (entries, racialTraits, etc.)
3. Parse speed object to get base walking speed integer
4. Convert size strings: "Medium" → "M", "Small" → "S", etc.
5. Extract language names from languageProficiencies

### 2.2 Classes Import

**Source**: `class/*.json` files
**Target Model**: `game_content.DnDClass`, `game_content.ClassFeature`, `game_content.Subclass`

#### Data Mapping - DnDClass
```
JSON Field          → Django Field
name                → name
entries             → description
primaryAbility      → primary_ability
hd.faces            → hit_die
(inferred)          → difficulty
proficiency.armor   → armor_proficiencies
proficiency.weapons → weapon_proficiencies
proficiency.saves   → saving_throw_proficiencies
skills.choose.count → skill_proficiency_count
skills.choose.from  → skill_proficiency_choices
```

#### Data Mapping - ClassFeature
```
JSON Field          → Django Field
(parent)            → dnd_class (FK)
name                → name
level               → level_acquired
entries             → description
type                → feature_type
(various)           → uses_per_rest
(various)           → choice_options
```

#### Transformation Rules
1. Parse class features from classFeatures arrays at each level
2. Extract subclass features separately
3. Map feature types based on content
4. Convert proficiency data to JSON arrays

### 2.3 Backgrounds Import

**Source**: `backgrounds.json`
**Target Model**: `game_content.Background`

#### Data Mapping
```
JSON Field          → Django Field
name                → name
entries             → description
feat                → origin_feat (lookup by name)
skillProficiencies  → skill_proficiencies
toolProficiencies   → tool_proficiencies
languageProficiencies → languages
startingEquipment   → equipment_options
(calculate)         → starting_gold
```

### 2.4 Feats Import

**Source**: `feats.json`
**Target Model**: `game_content.Feat`

#### Data Mapping
```
JSON Field          → Django Field
name                → name
entries             → description
(infer)             → feat_type
repeatable          → repeatable
prerequisite        → prerequisites
ability             → ability_score_increase
(various)           → benefits
```

#### Transformation Rules
1. Infer feat_type from tags or content analysis
2. Parse prerequisites into structured JSON
3. Extract ability score increases

## Phase 3: Equipment

### 3.1 Basic Equipment Import

**Source**: `items-base.json`, `items.json`
**Target Model**: `game_content.Equipment`, `game_content.Weapon`, `game_content.Armor`

#### Data Mapping - Equipment
```
JSON Field          → Django Field
name                → name
type                → equipment_type
value               → cost_gp (convert from cp)
weight              → weight
entries             → description
property            → properties
```

#### Data Mapping - Weapon
```
JSON Field          → Django Field
(inherit Equipment fields)
weaponCategory      → weapon_category
damage              → damage_dice
damageType          → damage_type
range               → range_normal, range_long
mastery             → mastery_property
```

#### Data Mapping - Armor
```
JSON Field          → Django Field
(inherit Equipment fields)
type                → armor_type
ac                  → base_ac
dexCap              → dex_bonus_limit
strength            → strength_requirement
stealth             → stealth_disadvantage
```

#### Transformation Rules
1. Convert cost from copper pieces to gold (divide by 100)
2. Parse damage strings like "1d6" for weapons
3. Extract range values from range objects
4. Map armor types to choices

## Phase 4: Spells

### 4.1 Spell Import

**Source**: `spells/*.json` files
**Target Model**: `game_content.Spell`

#### Data Mapping
```
JSON Field          → Django Field
name                → name
level               → spell_level
school              → school
time[0]             → casting_time
range               → range
duration            → duration
concentration       → concentration
ritual              → ritual
components.v        → components_v
components.s        → components_s
components.m        → components_m
components.m        → material_components (if string)
entries             → description
entriesHigherLevel  → higher_level_description
```

#### Transformation Rules
1. Parse time entries to match CASTING_TIME_CHOICES
2. Parse range to match RANGE_CHOICES
3. Parse duration to match DURATION_CHOICES
4. Extract material component descriptions
5. Combine entries arrays into single description

## Phase 5: Relationships

### 5.1 Spell-to-Class Relationships

**Process**:
1. Parse spell class lists from spell JSON
2. Match class names to DnDClass objects
3. Create M2M relationships

### 5.2 Feature-to-Subclass Relationships

**Process**:
1. Parse subclass features from class JSON
2. Match to existing ClassFeature objects
3. Create M2M relationships

### 5.3 Background-to-Feat Relationships

**Process**:
1. Match background feat names to Feat objects
2. Update Background origin_feat FK

## Implementation Structure

### Management Command Structure

```
management/
  commands/
    import_dnd_data.py      # Main orchestrator
    import_skills.py        # Phase 1.1
    import_languages.py     # Phase 1.2
    import_species.py       # Phase 2.1
    import_classes.py       # Phase 2.2
    import_backgrounds.py   # Phase 2.3
    import_feats.py        # Phase 2.4
    import_equipment.py     # Phase 3
    import_spells.py        # Phase 4
    link_relationships.py   # Phase 5
```

### Base Import Class

```python
class BaseImporter:
    def __init__(self, verbosity=1):
        self.verbosity = verbosity
        self.created_count = 0
        self.updated_count = 0
        self.skipped_count = 0
        self.errors = []

    def log(self, message, level=1):
        if self.verbosity >= level:
            print(message)

    def import_data(self):
        raise NotImplementedError

    def validate_entry(self, entry):
        raise NotImplementedError

    def transform_entry(self, entry):
        raise NotImplementedError

    def save_entry(self, transformed_data):
        raise NotImplementedError
```

## Error Handling Strategy

1. **Validation Errors**: Log and skip entry, continue processing
2. **Transformation Errors**: Log with full entry data, skip entry
3. **Database Errors**: Log, attempt rollback for entry, continue
4. **File Errors**: Fail entire import phase with clear message
5. **Relationship Errors**: Log missing references, continue

## Progress Tracking

- Display progress bars for large datasets
- Log summary statistics after each phase
- Save import logs to file with timestamp
- Option for dry-run mode to preview changes

## Testing Strategy

1. Create test fixtures with subset of data
2. Test each importer individually
3. Test full import on empty database
4. Test idempotency (running import twice)
5. Validate all relationships are created

## Performance Considerations

1. Use `bulk_create()` for large datasets when possible
2. Disable auto-commit and use transactions
3. Create indexes after bulk import
4. Process files in chunks for memory efficiency

## Next Steps

1. Implement BaseImporter class
2. Create individual importer classes for each phase
3. Build main orchestrator command
4. Add progress tracking and logging
5. Create test suite
6. Document usage instructions