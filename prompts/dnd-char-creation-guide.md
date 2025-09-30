# D&D Character Creation: Steps & Data Requirements

## Overview
This document outlines the step-by-step process for creating a D&D character (2024 Player's Handbook rules) and identifies all data structures needed for a character creation application.

---

## Character Creation Steps

### Step 1: Choose Class
**Purpose**: Establishes the character's core mechanical identity and determines their primary capabilities.

**Selection Process**:
- User chooses from 13 available classes
- System displays class overview information to aid decision

**Data Applied to Character**:
- Class name
- Level (starting at 1)
- Primary ability score
- Hit Point Die type
- Class features at level 1
- Starting equipment package chosen

### Step 2: Determine Origin

#### 2A: Choose Background
**Purpose**: Represents formative experiences before adventuring; provides ability score increases, skills, and starting feat.

**Selection Process**:
- User selects from available backgrounds
- May customize if allowed by DM

**Data Applied to Character**:
- Background name
- Ability Score Increases (+2 to one, +1 to another)
- Origin Feat
- Skill proficiencies (typically 2)
- Tool proficiencies
- Starting equipment OR gold

#### 2B: Choose Species
**Purpose**: Represents character heritage and provides innate abilities.

**Selection Process**:
- User selects from 10+ species options
- Note: Ability score increases now come from Background, not Species (2024 change)

**Data Applied to Character**:
- Species name
- Size category
- Speed
- Darkvision (if applicable)
- Special traits/abilities
- Languages (typically Common + 1-2 others)

### Step 3: Determine Ability Scores
**Purpose**: Defines character's core attributes that affect all mechanics.

**Methods Available**:
1. **Standard Array**: Assign pre-determined scores (15, 14, 13, 12, 10, 8)
2. **Point Buy**: Spend points to customize scores
3. **Random Roll**: Roll 4d6, drop lowest, six times

**Process**:
1. Generate base scores using chosen method
2. Apply Background ability score increases
3. Calculate ability modifiers: (Score - 10) ÷ 2, rounded down

**Data Applied to Character**:
- Six ability scores (with modifiers):
  - Strength
  - Dexterity
  - Constitution
  - Intelligence
  - Wisdom
  - Charisma

### Step 4: Choose Alignment
**Purpose**: Describes moral and ethical perspective (optional in many campaigns).

**Options**:
- Lawful Good, Neutral Good, Chaotic Good
- Lawful Neutral, True Neutral, Chaotic Neutral
- Lawful Evil, Neutral Evil, Chaotic Evil

**Data Applied to Character**:
- Alignment selection

### Step 5: Calculate Derived Statistics

**Process**: System automatically calculates based on previous choices.

**Calculated Values**:
- **Hit Points**: Class Hit Die maximum + Constitution modifier + species bonuses
- **Armor Class**: Base 10 + Dexterity modifier + armor/shield bonuses
- **Initiative**: Dexterity modifier
- **Proficiency Bonus**: +2 at level 1
- **Speed**: From species
- **Saving Throws**: Ability modifier + proficiency bonus (for proficient saves)
- **Skills**: Ability modifier + proficiency bonus (for proficient skills)
- **Passive Perception**: 10 + Wisdom (Perception) modifier

### Step 6: Fill in Personal Details
**Purpose**: Add narrative and personality elements.

**User Input Fields**:
- Character name
- Age
- Height
- Weight
- Physical description
- Personality traits
- Ideals
- Bonds
- Flaws
- Backstory

---

## Database Schema Requirements

### Core Tables

#### 1. CLASSES
```
- class_id (PK)
- class_name
- description
- primary_ability
- hit_die (d6, d8, d10, d12)
- armor_proficiencies (array)
- weapon_proficiencies (array)
- tool_proficiencies (array)
- saving_throw_proficiencies (array: 2 abilities)
- skill_proficiency_count (integer)
- available_skills (array)
- starting_equipment_options (JSON)
```

#### 2. CLASS_FEATURES
```
- feature_id (PK)
- class_id (FK)
- feature_name
- level_acquired
- description
- feature_type (passive, action, bonus_action, reaction)
- uses_per_rest (if applicable)
- requires_choice (boolean)
- choice_options (JSON, if applicable)
```

#### 3. SUBCLASSES
```
- subclass_id (PK)
- class_id (FK)
- subclass_name
- description
- level_available
- subclass_features (relationship to CLASS_FEATURES)
```

#### 4. BACKGROUNDS
```
- background_id (PK)
- background_name
- description
- ability_score_increases (JSON: e.g., {str: 2, con: 1})
- origin_feat_id (FK)
- skill_proficiencies (array)
- tool_proficiencies (array)
- equipment (text/JSON)
- starting_gold (integer)
```

#### 5. SPECIES (RACES)
```
- species_id (PK)
- species_name
- description
- size (Small, Medium, Large)
- speed (integer, in feet)
- darkvision_range (integer, 0 if none)
- languages (array)
- traits (relationship to SPECIES_TRAITS)
```

#### 6. SPECIES_TRAITS
```
- trait_id (PK)
- species_id (FK)
- trait_name
- description
- trait_type (passive, active, resistance, etc.)
- mechanical_effect (JSON describing game effect)
```

#### 7. FEATS
```
- feat_id (PK)
- feat_name
- feat_type (Origin, General, Fighting Style)
- description
- prerequisites (JSON)
- ability_score_increase (JSON, if applicable)
- benefits (JSON/text)
- repeatable (boolean)
```

#### 8. SKILLS
```
- skill_id (PK)
- skill_name
- associated_ability (STR, DEX, CON, INT, WIS, CHA)
- description
```

#### 9. EQUIPMENT
```
- equipment_id (PK)
- equipment_name
- equipment_type (weapon, armor, tool, adventuring_gear)
- cost_gp (decimal)
- weight (decimal)
- description
- properties (JSON)
```

#### 10. WEAPONS
```
- weapon_id (PK, FK to EQUIPMENT)
- weapon_category (Simple, Martial)
- damage_dice
- damage_type
- properties (array: versatile, finesse, heavy, etc.)
- mastery_property
- range (if ranged/thrown)
```

#### 11. ARMOR
```
- armor_id (PK, FK to EQUIPMENT)
- armor_type (Light, Medium, Heavy, Shield)
- base_ac
- dex_bonus_limit (null, 2, or 0)
- strength_requirement
- stealth_disadvantage (boolean)
```

#### 12. SPELLS
```
- spell_id (PK)
- spell_name
- spell_level (0-9, 0 for cantrips)
- school (Abjuration, Conjuration, etc.)
- casting_time
- range
- components (V, S, M)
- material_components (text)
- duration
- concentration (boolean)
- description
- higher_level_description
- available_to_classes (array of class_ids)
```

#### 13. LANGUAGES
```
- language_id (PK)
- language_name
- script
- typical_speakers
- rarity (Common, Uncommon, Rare, Exotic)
```

### Character Storage Tables

#### 14. CHARACTERS
```
- character_id (PK)
- user_id (FK)
- character_name
- class_id (FK)
- subclass_id (FK, nullable)
- background_id (FK)
- species_id (FK)
- level
- experience_points
- alignment
- current_hp
- max_hp
- temporary_hp
- armor_class
- initiative
- speed
- proficiency_bonus
- inspiration (boolean)
- created_date
- last_modified_date
```

#### 15. CHARACTER_ABILITIES
```
- id (PK)
- character_id (FK)
- strength_score
- dexterity_score
- constitution_score
- intelligence_score
- wisdom_score
- charisma_score
```

#### 16. CHARACTER_SKILLS
```
- id (PK)
- character_id (FK)
- skill_id (FK)
- proficiency_type (none, proficient, expertise)
```

#### 17. CHARACTER_SAVING_THROWS
```
- id (PK)
- character_id (FK)
- ability_name
- is_proficient (boolean)
```

#### 18. CHARACTER_EQUIPMENT
```
- id (PK)
- character_id (FK)
- equipment_id (FK)
- quantity
- equipped (boolean)
- attuned (boolean, for magic items)
```

#### 19. CHARACTER_SPELLS
```
- id (PK)
- character_id (FK)
- spell_id (FK)
- always_prepared (boolean)
- prepared (boolean)
```

#### 20. CHARACTER_FEATURES
```
- id (PK)
- character_id (FK)
- feature_id (FK)
- uses_remaining (integer, if applicable)
- choice_made (text/JSON, if feature requires choice)
```

#### 21. CHARACTER_FEATS
```
- id (PK)
- character_id (FK)
- feat_id (FK)
- source (background, class, ASI)
- choice_made (JSON, if feat has options)
```

#### 22. CHARACTER_LANGUAGES
```
- id (PK)
- character_id (FK)
- language_id (FK)
```

#### 23. CHARACTER_PROFICIENCIES
```
- id (PK)
- character_id (FK)
- proficiency_type (armor, weapon, tool, saving_throw, skill)
- proficiency_name
```

#### 24. CHARACTER_DETAILS
```
- id (PK)
- character_id (FK)
- age
- height
- weight
- eyes
- skin
- hair
- personality_traits (text)
- ideals (text)
- bonds (text)
- flaws (text)
- backstory (text)
- notes (text)
```

---

## Key Data Relationships

### Class Selection Flow
1. User selects **CLASS** → System loads:
   - Available **CLASS_FEATURES** for level 1
   - **SUBCLASSES** (if available at level 1)
   - Skill options from available_skills
   - Starting **EQUIPMENT** options
   - **FEATS** (if class grants feat at level 1, like Fighting Style)

### Background Selection Flow
1. User selects **BACKGROUND** → System loads:
   - Ability score increases to apply
   - Associated **FEAT** (Origin feat)
   - **SKILLS** proficiencies
   - Tool proficiencies
   - Starting **EQUIPMENT** or gold

### Species Selection Flow
1. User selects **SPECIES** → System loads:
   - **SPECIES_TRAITS**
   - **LANGUAGES** (Common + species defaults)
   - Base movement speed
   - Size category

### Ability Score Application
1. User generates/assigns base scores
2. System applies Background bonuses
3. System calculates modifiers
4. Modifiers feed into:
   - **Saving throws** (with proficiency where applicable)
   - **Skills** (with proficiency where applicable)
   - Hit Points (Constitution modifier)
   - Armor Class (Dexterity modifier + armor)
   - Attack rolls (STR or DEX for weapons)
   - Spell save DC (spellcasting ability modifier)

### Equipment & Combat Stats
1. Selected **ARMOR** → Determines base AC calculation
2. Selected **WEAPONS** → Determines:
   - Attack bonus (ability modifier + proficiency)
   - Damage dice and type
   - Weapon mastery property (if class has Weapon Mastery)
3. System calculates:
   - Attack rolls: 1d20 + ability modifier + proficiency bonus
   - Damage rolls: weapon dice + ability modifier

---

## Additional Data Considerations

### Spell Preparation & Casting
For spellcasting classes:
- **Spell slots** by level (from class table)
- **Spells known** vs **Prepared spells** (class-dependent)
- **Spellcasting ability** (from class)
- **Spell save DC**: 8 + proficiency bonus + spellcasting ability modifier
- **Spell attack bonus**: proficiency bonus + spellcasting ability modifier

### Conditions & Status Effects
While not part of character creation, the app should support:
- Conditions (Blinded, Charmed, Frightened, etc.)
- Death saves tracking
- Exhaustion levels
- Temporary effects

### Level Advancement
Future consideration for tracking:
- Experience thresholds
- Features gained per level
- Ability Score Improvements (ASI) at specific levels
- Spell slot progression
- Hit point increases on level up

### Multiclassing (Advanced)
If supporting multiclassing:
- Prerequisites (minimum ability scores)
- Proficiencies gained/not gained
- Spell slot calculation for multi-class casters
- Class feature restrictions

---

## UI/UX Flow Recommendations

### Progressive Disclosure
1. **Class Selection** (with comparison tool)
2. **Background Selection** (filtered by desired ability bonuses)
3. **Species Selection** (with trait previews)
4. **Ability Score Generation** (showing how scores affect build)
5. **Equipment & Spells** (class-appropriate options)
6. **Details & Personality** (narrative elements)
7. **Review & Finalize** (complete character sheet preview)

### Validation Rules
- All required choices made before advancing
- Ability scores within valid ranges (3-20 typically)
- Equipment weight vs carrying capacity
- Spell selection within limits
- Prerequisite requirements met

### Helpful Features
- **Build Guides**: Suggested combinations for specific playstyles
- **Tooltips**: Explain game terms and mechanics
- **Character Sheet Preview**: Real-time updates as selections made
- **Save Progress**: Allow partially completed characters
- **Import/Export**: Character data portability
- **Dice Roller**: For ability score rolling method

---

## API Endpoints Needed

```
GET /api/classes - List all classes
GET /api/classes/:id - Get class details with features
GET /api/backgrounds - List all backgrounds
GET /api/backgrounds/:id - Get background details
GET /api/species - List all species
GET /api/species/:id - Get species with traits
GET /api/feats - List all feats (filtered by type)
GET /api/equipment - List equipment (filterable)
GET /api/spells - List spells (filterable by class, level)
GET /api/skills - List all skills

POST /api/characters - Create new character
GET /api/characters/:id - Get character data
PUT /api/characters/:id - Update character
DELETE /api/characters/:id - Delete character
GET /api/characters/:id/sheet - Get formatted character sheet
```

---

## Notes on 2024 vs 2014 Rules

### Key Changes in 2024:
- **Step order changed**: Class → Background → Species (was Species → Class → Background)
- **Ability Score Increases**: Now from Background, not Species
- **Origin Feats**: All backgrounds grant a feat at level 1
- **Weapon Mastery**: New feature for martial classes
- **Streamlined Features**: Many class features simplified or reorganized
- **Species Traits**: No longer provide ability score bonuses

### Backward Compatibility:
If supporting older content:
- Legacy backgrounds: User manually applies +2/+1 or +1/+1/+1 and selects Origin feat
- Legacy species: Ignore any printed ability score bonuses
