# D&D Data ETL Usage Guide

## Overview

The D&D Character Creator includes a comprehensive ETL (Extract, Transform, Load) system for importing D&D 5e game data from JSON files into the Django database.

## Quick Start

### Import All Data
```bash
python manage.py import_dnd_data
```

### Import with Options
```bash
# Clear existing data before importing
python manage.py import_dnd_data --clear

# Run in dry-run mode (preview only, no database changes)
python manage.py import_dnd_data --dry-run

# Import only a specific phase
python manage.py import_dnd_data --phase 1

# Specify custom data directory
python manage.py import_dnd_data --data-dir /path/to/data

# Increase verbosity for debugging
python manage.py import_dnd_data -v 2
```

## Import Phases

The import process is organized into 5 phases that must be run in order:

### Phase 1: Core Reference Data
- **Skills** (18 core D&D skills)
- **Languages** (Standard and exotic languages)

### Phase 2: Character Options
- **Species** (Races and their traits)
- **Classes** (Character classes with features)
- **Backgrounds** (Character backgrounds)
- **Feats** (Origin, general, and fighting style feats)

### Phase 3: Equipment
- **Weapons** (Simple and martial weapons)
- **Armor** (Light, medium, and heavy armor)
- **Equipment** (Adventuring gear, tools, etc.)

### Phase 4: Spells
- **Spells** (Cantrips through 9th level)
- Spell components, duration, range, etc.

### Phase 5: Relationships
- Link spells to classes
- Link features to subclasses
- Link origin feats to backgrounds

## Individual Import Commands

You can also run individual importers:

### Import Skills Only
```bash
python manage.py import_skills
python manage.py import_skills --clear  # Clear existing skills first
python manage.py import_skills --dry-run  # Preview mode
```

### Import Languages Only
```bash
python manage.py import_languages
python manage.py import_languages --clear
python manage.py import_languages --dry-run
```

## Data Source

The importers expect JSON data files in the `data/` directory:

```
data/
├── skills.json
├── languages.json
├── races.json
├── backgrounds.json
├── feats.json
├── class/
│   ├── class-artificer.json
│   ├── class-barbarian.json
│   ├── class-bard.json
│   └── ...
├── spells/
│   ├── spells-phb.json
│   ├── spells-xge.json
│   └── ...
├── items.json
└── items-base.json
```

## Filtering Strategy

The importers automatically filter content to include only official 5e sources:

**Included Sources**: PHB, XGE, TCE, SCAG, and all other official WotC publications

**Excluded Sources**:
- XPHB (2024 edition content)
- UA (Unearthed Arcana)
- Homebrew content

## Troubleshooting

### Common Issues

1. **"Data directory not found"**
   - Ensure the `data/` directory exists in your project root
   - Or specify the correct path: `--data-dir /path/to/data`

2. **Import failures**
   - Run with higher verbosity: `-v 2` or `-v 3`
   - Check the specific error messages
   - Try running individual importers to isolate issues

3. **Duplicate key errors**
   - Use the `--clear` flag to remove existing data
   - Or run without `--clear` to update existing entries

### Viewing Import Results

After importing, you can verify the data:

1. **Django Admin**
   ```bash
   python manage.py runserver
   ```
   Then visit http://localhost:8000/admin/

2. **Django Shell**
   ```bash
   python manage.py shell
   ```
   ```python
   from game_content.models import Skill, Language
   Skill.objects.count()  # Should show 18
   Language.objects.filter(rarity='exotic').count()
   ```

## Development

### Creating New Importers

New importers should extend the `BaseImporter` class:

```python
from .base_importer import BaseImporter
from game_content.models import YourModel

class Command(BaseImporter):
    help = 'Import data for YourModel'

    def clear_existing_data(self):
        YourModel.objects.all().delete()

    def import_data(self):
        # Load and process data
        pass

    def validate_entry(self, entry):
        # Validate data
        return True

    def transform_entry(self, entry):
        # Transform from JSON to model format
        return {...}

    def save_entry(self, transformed_data):
        # Save to database
        YourModel.objects.update_or_create(...)
```

### Testing Importers

Run tests with:
```bash
python manage.py test game_content.tests.test_importers
```

## Next Steps

After successfully importing data:

1. Verify all data is imported correctly in Django admin
2. Create test characters to ensure relationships work
3. Run the application and test character creation flow
4. Consider creating database backups after successful imports