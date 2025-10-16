# Data Alignment Findings and Recommendations

## Step 4: Review of Data Alignment

### Summary of Analysis

We have analyzed the JSON data structure in the `data/` directory and mapped it to our Django database schema. The data is sourced from various D&D 5e sourcebooks and is well-structured for import.

### Data Alignment Findings

#### ✅ Good Matches
1. **Skills** (`skills.json`)
   - 36 skills with clean mapping
   - Direct field mapping: name, ability, description

2. **Languages** (`languages.json`)
   - 169 languages available
   - Will need to infer script and rarity classification

3. **Feats** (`feats.json`)
   - 192 feats available
   - Need to categorize by type (origin/general/fighting_style)

4. **Classes & Features** (`class/*.json`)
   - 13 official classes plus variants
   - Comprehensive feature data by level
   - Subclasses with associated features

5. **Backgrounds** (`backgrounds.json`)
   - 142 backgrounds from various sources
   - Includes skill/tool/language proficiencies

6. **Spells** (`spells/*.json`)
   - Hundreds of spells across multiple sourcebooks
   - Complete spell data including components, duration, etc.

#### ⚠️ Challenges Identified
1. **Species/Races**: JSON uses "race" terminology vs our "Species" model
2. **Equipment**: Split between magic items and mundane items
3. **Data Transformation**: Many fields are arrays/objects requiring parsing
4. **Edition Mixing**: Contains both 5e and 2024 content
5. **Multiple Sources**: Data from PHB, XGE, TCE, SCAG, etc.

### Decisions Made

Based on user input, we will proceed with the following approach:

1. **Sourcebook Inclusion**: Include ALL official content
   - PHB (Player's Handbook)
   - XGE (Xanathar's Guide to Everything)
   - TCE (Tasha's Cauldron of Everything)
   - SCAG (Sword Coast Adventurer's Guide)
   - All other official WotC publications

2. **Edition**: Focus on 5e content only
   - Filter out 2024/5.5e content (marked as "edition": "2024" or source "XPHB")
   - Use traditional 5e rules and data

3. **Subraces**: Treat as separate species
   - Each subrace will be its own Species entry
   - Example: "Elf" and "High Elf" as separate Species records
   - Maintain racial traits specific to each

4. **Homebrew/UA**: Skip for now
   - Exclude Mystic class
   - Exclude Unearthed Arcana content
   - Focus on officially published material only

### Recommended ETL Approach

#### Phase 1: Core Reference Data
1. Skills
2. Languages
3. Ability Scores (constants)

#### Phase 2: Character Options
1. Species (Races) and Traits
2. Classes and Class Features
3. Subclasses
4. Backgrounds
5. Feats

#### Phase 3: Equipment
1. Base equipment (mundane items)
2. Weapons
3. Armor
4. Adventuring gear

#### Phase 4: Spells
1. Spell data
2. Class spell lists (M2M relationships)

#### Phase 5: Relationships
1. Link spells to classes
2. Link features to subclasses
3. Validate all foreign key relationships

### Data Filtering Strategy

For each data import, we will:
1. Filter by source to exclude unofficial content
2. Filter by edition to exclude 2024 content
3. Handle missing/null fields with sensible defaults
4. Transform complex objects/arrays into appropriate format
5. Maintain data integrity with proper error handling

### Next Steps

1. Create ETL plan document with detailed transformation rules
2. Build data loading script with progress tracking
3. Implement validation and error handling
4. Test with small data subsets first
5. Run full import with logging