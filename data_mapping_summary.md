# JSON Data to Database Schema Mapping

## 1. Skills
- **JSON Source**: `data/skills.json`
- **JSON Structure**: Root object with `skill` array
- **Database Model**: `Skill`
- **Mapping**:
  - `name` → `name`
  - `ability` → `associated_ability` (needs mapping: STR/DEX/CON/INT/WIS/CHA)
  - `entries` → `description` (array of text, needs concatenation)

## 2. Languages
- **JSON Source**: `data/languages.json`
- **JSON Structure**: Root object with `language` array
- **Database Model**: `Language`
- **Mapping**:
  - `name` → `name`
  - `typicalSpeakers` → `typical_speakers` (array, needs joining)
  - Script needs to be inferred or set to default
  - Rarity needs to be determined (standard vs exotic)

## 3. Feats
- **JSON Source**: `data/feats.json`
- **JSON Structure**: Root object with `feat` array
- **Database Model**: `Feat`
- **Mapping**:
  - `name` → `name`
  - `entries` → `description` (array, needs concatenation)
  - `prerequisite` → `prerequisites` (array of objects)
  - `ability` → `ability_score_increase` (if present)
  - Need to determine `feat_type` (origin/general/fighting_style)
  - `repeatable` field may be in the data

## 4. Species (Races)
- **JSON Source**: `data/races.json`
- **JSON Structure**: Root object with `race` and `subrace` arrays
- **Database Model**: `Species` and `SpeciesTrait`
- **Mapping**:
  - `name` → `name`
  - `size` → `size` (array, need to pick primary)
  - `speed` → `speed` (object with walk/fly/swim)
  - `darkvision` → `darkvision_range`
  - `languageProficiencies` → `languages` (array of objects)
  - `entries` → Create `SpeciesTrait` records
  - Subraces might be handled as variants or separate species

## 5. Classes
- **JSON Source**: `data/class/class-*.json`
- **JSON Structure**: Each file has `class`, `subclass`, `classFeature`, `subclassFeature` arrays
- **Database Models**: `DnDClass`, `Subclass`, `ClassFeature`
- **Mapping**:
  - Class: `name` → `name`, `hd` → `hit_die`
  - Need to determine `primary_ability` from class data
  - `proficiency` → Extract armor/weapon/saving throw proficiencies
  - ClassFeature: `name` → `name`, `level` → `level_acquired`
  - Subclass: `name` → `name`, features need M2M relationship

## 6. Backgrounds
- **JSON Source**: `data/backgrounds.json`
- **JSON Structure**: Root object with `background` array
- **Database Model**: `Background`
- **Mapping**:
  - `name` → `name`
  - `entries` → `description`
  - `skillProficiencies` → `skill_proficiencies`
  - `languageProficiencies` → `languages`
  - `startingEquipment` → `equipment_options`
  - Need to handle Origin Feat association (2024 rules)

## 7. Equipment/Weapons/Armor
- **JSON Sources**: `data/items.json`, `data/items-base.json`
- **JSON Structure**: `baseitem` array in items-base.json
- **Database Models**: `Equipment`, `Weapon`, `Armor`
- **Mapping**:
  - `name` → `name`
  - `type` → `equipment_type`
  - `weight` → `weight`
  - `value` → `cost_gp` (needs conversion from cp/sp/gp)
  - Weapons: `dmg1` → `damage_dice`, `dmgType` → `damage_type`
  - Armor: `ac` → `base_ac`, determine armor type

## 8. Spells
- **JSON Source**: `data/spells/spells-*.json`
- **JSON Structure**: Each file has `spell` array
- **Database Model**: `Spell`
- **Mapping**:
  - `name` → `name`
  - `level` → `spell_level`
  - `school` → `school` (single letter to full name)
  - `time` → `casting_time` (array of objects)
  - `range` → `range` (object)
  - `components` → Parse to `components_v/s/m`
  - `duration` → `duration` (array of objects)
  - `entries` → `description`
  - Need to map spell-to-class relationships

## Key Challenges:
1. **Data Transformation**: Many fields are arrays/objects that need parsing
2. **Edition Handling**: Mix of 5e and 2024 (5.5e) content
3. **Relationships**: Need to establish FK relationships after initial load
4. **Missing Data**: Some required fields may not be in source data
5. **Data Volume**: Thousands of items, hundreds of spells
6. **Source Filtering**: Multiple sources (PHB, XGE, TCE, etc.) - need to decide which to include