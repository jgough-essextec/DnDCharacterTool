# D&D Character Creator - Detailed User Journey

## Overview
This document maps the complete user experience for creating a D&D character, including all UI components, user interactions, data flows, and API calls for each step.

---

## Landing Page / Character List

### Purpose
Entry point where users can start a new character or manage existing ones.

### UI Components
- **Header**
  - App logo/branding
  - User profile dropdown (settings, logout)
  - Help/tutorial link

- **Main Content**
  - Hero section with "Create New Character" CTA button
  - Character cards grid showing existing characters
    - Character portrait/avatar
    - Character name
    - Level, class, species summary
    - Quick actions: Edit, Delete, View Sheet, Duplicate
  - Empty state if no characters (encouraging message + create button)

- **Filters/Sorting** (if many characters)
  - Sort by: Date created, Name, Level, Class
  - Filter by: Class, Level range

### User Actions
1. Click "Create New Character" → Navigate to Step 1
2. Click existing character → View full character sheet
3. Click "Edit" on character → Resume at last step or go to summary
4. Click "Delete" → Confirmation modal → Delete character

### API Calls
```
GET /api/user/characters
- Returns: Array of user's characters with summary data

DELETE /api/characters/:id
- Returns: Success confirmation

POST /api/characters/:id/duplicate
- Returns: New character ID
```

### Data Required
- User authentication state
- List of user's existing characters

---

## Step 1: Choose Your Class

### Page Header
- Progress indicator: "Step 1 of 6: Choose Your Class"
- Back button (to character list)
- Save & Exit button (saves draft)

### UI Components

#### Main Section: Class Selection Grid
- **Card-based layout** (responsive grid: 3-4 columns on desktop)
- Each class card displays:
  - Class icon/illustration
  - Class name
  - Primary ability badge (e.g., "Strength" with icon)
  - Difficulty indicator (⭐⭐⭐ - Beginner/Intermediate/Advanced)
  - One-line description (e.g., "Master of martial combat")
  - "Learn More" hover/click

#### Class Details Panel (Slide-out or Modal)
Opens when user clicks card or "Learn More"

**Overview Tab**
- Full class description (2-3 paragraphs)
- Role in party (Tank, Damage Dealer, Support, Control, Utility)
- Playstyle keywords (tags: "Melee", "Spellcaster", "Versatile", etc.)

**Core Traits Tab**
- Primary Ability: Large display with explanation
- Hit Point Die: Visual representation (d6 - d12)
- Saving Throw Proficiencies: List with tooltips
- Armor/Weapon Training: Icons showing what they can use
- Starting Skill Proficiencies: How many they get + available list

**Level 1 Features Tab**
- Expandable sections for each feature
  - Feature name
  - Description
  - Mechanical details
  - Usage (Action, Bonus Action, Passive, etc.)

**Level Progression Preview**
- Table showing key levels and major features gained
- Highlights levels 3, 5, 11, 17, 20 (major power spikes)

**Starting Equipment Preview**
- Shows typical starting gear
- Note about choices made later

**Subclass Preview** (if applicable)
- When subclass is chosen (level 1 or 3)
- List of available subclasses with 1-line descriptions

#### Comparison Feature
- "Compare Classes" button
- Side-by-side view of up to 3 classes
- Highlights differences in abilities, features, complexity

#### Recommendation Quiz (Optional)
- "Not sure? Take our quiz!" link
- 5-7 questions about playstyle preferences
  - "Do you prefer up-close combat or attacking from range?"
  - "Do you like managing lots of options or keeping it simple?"
  - "Do you want to cast spells?"
- Results suggest 2-3 classes

### Selection Interaction
1. User browses/compares classes
2. User clicks "Choose [Class Name]" button on a card
3. Confirmation animation
4. Class-specific choices appear (if any)

### Class-Specific Choices (Conditional)

**For All Classes:**
- **Skill Proficiency Selection**
  - Header: "Choose [X] skills from your class list"
  - Available skills displayed as cards/chips
  - Each shows: Skill name, associated ability, brief description
  - Selected skills highlighted/checked
  - Validation: Must select exactly X skills

**For Spellcasting Classes (Wizard, Cleric, Druid, Bard, etc.):**
- **Cantrip Selection** (if applicable)
  - "Choose [X] cantrips"
  - Searchable/filterable spell grid
  - Each spell card shows:
    - Spell name
    - School of magic badge
    - Casting time
    - Range
    - Components (V, S, M)
    - Short description
    - "View Full Details" expands full spell info
  - Selected spells highlighted

- **Prepared Spells Selection** (for prepared casters)
  - "Choose [X] 1st-level spells"
  - Same interface as cantrips
  - Counter showing selections (e.g., "3 / 5 selected")

**For Fighter (and other martial classes with options):**
- **Fighting Style Selection**
  - "Choose a Fighting Style"
  - Cards showing each fighting style feat
  - Each displays: Name, full description, tactical use case
  - Only one selectable (radio button behavior)

**For Weapon Mastery Classes:**
- **Weapon Mastery Selection**
  - "Choose [X] weapons to master"
  - Grouped by category: Simple Melee, Martial Melee, Ranged
  - Each weapon shows:
    - Name, damage dice, damage type
    - Properties (Versatile, Finesse, etc.)
    - Mastery property (Graze, Sap, Slow, etc.) with tooltip
  - Suggestions based on starting equipment

**For Warlock:**
- **Otherworldly Patron** (Subclass at level 1)
  - Must choose patron
  - Similar to subclass selection interface

### Bottom Action Bar
- Validation summary: "Complete all required selections to continue"
- Visual checklist of requirements:
  - ✓ Class selected
  - ✓ Skills selected (3/3)
  - ✓ Fighting Style chosen
  - ✓ Weapons mastered (3/3)
- "Continue to Origin" button (disabled until all complete)
- Character sheet preview drawer (shows live updates)

### API Calls
```
GET /api/classes
- Returns: Array of all classes with summary data
- Response includes: id, name, icon_url, primary_ability, difficulty, description_short

GET /api/classes/:id
- Returns: Complete class details
- Includes: features, proficiencies, subclasses, spell_lists, equipment_options

GET /api/spells?class_id=X&level=0,1
- Returns: Available spells for class
- Filters: level, school, ritual, concentration

POST /api/characters (draft)
- Payload: { class_id, skill_selections, fighting_style, etc. }
- Returns: character_id (for saving progress)

PUT /api/characters/:id/class
- Payload: All class-related choices
- Returns: Updated character object
```

### Validation Rules
- Class must be selected
- All required skill selections made (exact count)
- Fighting style chosen (if applicable)
- Weapon masteries selected (if applicable)
- Cantrips and spells chosen (if spellcaster)
- No duplicate selections

### Help & Tooltips
- Hover tooltips on all game terms
- "?" info icons with expanded explanations
- "What's a saving throw?" type educational popups
- Context-sensitive help sidebar

---

## Step 2: Determine Your Origin

### Page Header
- Progress indicator: "Step 2 of 6: Determine Your Origin"
- Back button (returns to Step 1, preserves selections)
- Character preview widget (shows class choice)

### Layout
Two-part selection: Background first, then Species

---

## Step 2A: Choose Your Background

### UI Components

#### Background Selection Interface
- **Tab switcher or segmented control**
  - "Choose Background" (active)
  - "Choose Species" (locked until background chosen)

#### Background Cards Grid
- Similar visual style to class cards
- Each card shows:
  - Background name
  - Thematic icon
  - One-line description
  - Key proficiencies preview (icons for tools/skills)
  - "View Details" button

#### Background Details Panel

**Overview Tab**
- Full background description
- Narrative flavor text
- Typical character archetypes

**Mechanical Benefits Tab**
- **Ability Score Increases** (most important)
  - Large display: "+2 [Ability], +1 [Ability]"
  - Explanation of how this works
  - Synergy indicator if matches class primary ability
  
- **Origin Feat**
  - Feat name with icon
  - Full feat description
  - Tactical applications

- **Skill Proficiencies**
  - List with ability associations
  - Shows if any overlap with class skills

- **Tool Proficiencies**
  - Icons and names
  - Tooltip explaining what each tool does

- **Starting Equipment**
  - Option A: Equipment package list
  - Option B: Gold amount (typically 50 GP)

**Synergy Indicator**
- "Great for [Your Class]!" badge if good match
- "Recommended" if ability increases match class
- Warning if poor synergy (different primary abilities)

#### Smart Recommendations
- "Recommended for [Your Class]" section at top
- Sorted by synergy with chosen class
- Filter options:
  - "Best for my class"
  - "Combat-focused"
  - "Social-focused"
  - "Exploration-focused"
  - "Show all"

#### Custom Background Option
- "Create Custom Background" button
- Opens wizard for customization:
  - Choose ability score increases (+2/+1 or +1/+1/+1)
  - Choose 2 skill proficiencies from master list
  - Choose 1 tool proficiency
  - Select 1 Origin feat from list
  - Write custom background description
  - Choose equipment package or gold

### Origin Feat Details
When background is selected, if feat needs clarification:
- Automatic expansion showing full feat rules
- If feat has choices (like Magic Initiate), selection interface appears
  - Choose class for spell list
  - Choose cantrips and 1st-level spell
  - Visual spell selector (same as Step 1)

### Selection Interaction
1. User explores backgrounds
2. Clicks "Choose [Background Name]"
3. If Origin feat has choices → Make those choices
4. Confirmation, then Species tab unlocks

### API Calls
```
GET /api/backgrounds
- Returns: Array of backgrounds with summary
- Optional query param: ?recommended_for_class=X

GET /api/backgrounds/:id
- Returns: Complete background details
- Includes: ability_increases, feat, proficiencies, equipment_options

GET /api/feats?type=origin
- Returns: All origin feats for custom background

PUT /api/characters/:id/background
- Payload: { background_id, equipment_choice, feat_choices }
- Returns: Updated character with ability scores applied
```

---

## Step 2B: Choose Your Species

### UI Components

#### Species Selection Grid
- Card layout (2-3 columns)
- Each card shows:
  - Species illustration
  - Species name
  - Size and speed icons
  - Key trait preview (1-2 major abilities)
  - "Learn More" button

#### Species Details Panel

**Overview Tab**
- Species description and lore
- Typical cultures and societies
- Physical appearance descriptions
- Naming conventions

**Traits Tab**
- **Size**: Small, Medium, or Large with explanation
- **Speed**: Walking speed in feet, special movement if any
- **Darkvision**: Range in feet (if applicable) with night vision icon
- **Special Abilities**: Each trait in expandable card
  - Trait name
  - Description
  - Mechanical effect
  - Usage frequency (always on, X/day, etc.)

**Languages Tab**
- Common (automatic)
- Species default language(s)
- Additional language choices (if any)
- Dropdown to select from available languages

**Variant Options** (if applicable)
- Some species have subtypes/variants
- Selection buttons if needed (e.g., Hill Dwarf vs Mountain Dwarf)

#### Language Selection (if species grants choice)
- "Choose [X] additional language(s)"
- Searchable dropdown or modal
- Languages categorized:
  - Standard (Common, Elvish, Dwarvish, etc.)
  - Exotic (Draconic, Primordial, etc.)
  - Rare/Unusual
- Each shows: Name, script, typical speakers

### Selection Interaction
1. User browses species
2. Clicks "Choose [Species Name]"
3. If variant exists → Choose variant
4. If additional languages granted → Choose languages
5. Confirmation animation
6. Preview of complete origin (Background + Species) displayed

### Combined Origin Summary
After both selections:
- **Summary card appears**
  - "Your Origin is Complete!"
  - Shows both background and species
  - Lists all benefits gained:
    - Ability score increases applied
    - Origin feat
    - All proficiencies (skills, tools)
    - Languages known
    - Species traits
  - Equipment received

### API Calls
```
GET /api/species
- Returns: Array of all species with summary data

GET /api/species/:id
- Returns: Complete species details
- Includes: traits, languages, variants, size, speed

GET /api/languages
- Returns: All available languages

PUT /api/characters/:id/species
- Payload: { species_id, variant_id, language_selections, trait_choices }
- Returns: Updated character with all origin data applied
```

### Bottom Action Bar
- Progress checklist:
  - ✓ Background chosen
  - ✓ Species chosen
  - ✓ Languages selected
- "Continue to Ability Scores" button
- "Back to Background" button (if need to change)

---

## Step 3: Determine Your Ability Scores

### Page Header
- Progress indicator: "Step 3 of 6: Determine Your Ability Scores"
- Character summary widget (shows class, background, species)

### UI Components

#### Method Selection
Large, clear cards for choosing generation method:

**Standard Array Card**
- Title: "Standard Array (Recommended for Beginners)"
- Description: "Use a pre-set array of ability scores"
- Icon: Six dice showing fixed values
- "Choose This Method" button
- Pros listed: Fast, balanced, fair
- Available scores preview: 15, 14, 13, 12, 10, 8

**Point Buy Card**
- Title: "Point Buy (Customize Your Stats)"
- Description: "Spend 27 points to build custom scores"
- Icon: Shopping cart with point tokens
- "Choose This Method" button
- Pros listed: Flexible, balanced, strategic
- Point range preview: Scores from 8-15

**Roll Dice Card**
- Title: "Roll Dice (Classic Method)"
- Description: "Roll 4d6, drop lowest, six times"
- Icon: Tumbling dice
- "Choose This Method" button
- Pros listed: Exciting, random, can be powerful
- Warning: "Results can be very different!"

### Method-Specific Interfaces

---

### Option A: Standard Array

#### Display
- Six large boxes showing available scores: **15, 14, 13, 12, 10, 8**
- Six ability score slots below (draggable or clickable):
  - Each slot shows:
    - Ability name (Strength, Dexterity, etc.)
    - Ability icon
    - Brief description of what it does
    - Which classes use it (badges)
    - Empty state: "Drag score here" or "Click to assign"
    - When assigned: The score value
    - Background bonus applied: "+ X from [Background]" 
    - Final score with modifier in parentheses

#### Interaction Flow
**Method 1: Drag & Drop**
1. User drags score from available pool
2. Drops onto ability slot
3. Score removed from pool
4. Applied bonuses calculated and shown
5. Can drag to swap between abilities

**Method 2: Click to Assign**
1. User clicks empty ability slot
2. Available scores highlight
3. User clicks score to assign
4. Score applied and removed from pool
5. Click assigned score to unassign

#### Smart Suggestions
- "Suggested Assignment" button
  - Auto-assigns scores optimally for chosen class
  - Shows reasoning: "15 → Strength (your class primary ability)"
  - User can still modify after

- Visual indicators:
  - Green highlight: "Great choice for your class!"
  - Yellow highlight: "Good choice"
  - Red highlight: "This ability isn't important for your class"

#### Real-Time Impact Display
Side panel showing how ability scores affect character:

**Combat Stats**
- Attack bonus: +X (from Strength or Dexterity)
- Armor Class: X (from Dexterity + armor)
- Initiative: +X (from Dexterity)

**Hit Points**
- Starting HP calculation shown:
  - Base: [Class Hit Die max] (e.g., 10 for Fighter)
  - + Constitution modifier: +X
  - + Species bonus: +X (if any, like Dwarf Toughness)
  - = Total: XX HP

**Skills**
- List of proficient skills with bonuses calculated
- Shows how ability scores affect each

**Saving Throws**
- Proficient saves with bonuses shown
- Non-proficient saves listed

**Spellcasting** (if applicable)
- Spell save DC: 8 + proficiency + [ability] mod
- Spell attack bonus: proficiency + [ability] mod

---

### Option B: Point Buy

#### Display
- **Point Pool Counter** (large, prominent)
  - "27 points remaining" (updates live)
  - Color-coded: Green (plenty left) → Yellow (running low) → Red (overspent)

- **Six Ability Score Builders**
  - Each shows:
    - Ability name and icon
    - Current score (starts at 8)
    - Point cost to increase/decrease
    - +/- buttons or slider
    - Background bonus shown separately: "+ X"
    - Final score: [Base] + [Bonus] = [Total] ([Modifier])

#### Point Cost Table (visible reference)
```
Score | Cost  | Score | Cost
------|-------|-------|------
  8   |  0    |  12   |  4
  9   |  1    |  13   |  5
 10   |  2    |  14   |  7
 11   |  3    |  15   |  9
```

#### Interaction
1. User clicks + button or drags slider
2. Point cost deducted from pool
3. Background bonus applied
4. Final modifier calculated
5. Real-time impact display updates

#### Constraints
- Scores cannot go below 8 or above 15 (before racial bonuses)
- Cannot spend more than 27 points
- Warning if trying to exceed limits

#### Presets
- "Reset" button (back to all 8s)
- "Standard Array Equivalent" button
- "Balanced Build" button (spreads evenly)
- "Min-Max Build" button (optimized for class)

#### Same Impact Display
- Real-time stats update as in Standard Array

---

### Option C: Roll Dice

#### Initial Rolling Interface
- **Roll Animation Area**
  - Large "Roll Your Ability Scores" button
  - Animated 3D dice rolling (visual excitement)
  - Sounds optional (dice clattering)

- **Rolling Process**
  - "Rolling for Ability Score #1..."
  - Shows 4 dice rolling: 4d6
  - Drops lowest die (visual strikethrough)
  - Sum displayed: "Total: X"
  - Die rolls stored in results area
  - Automatically proceeds to next roll
  - Repeat 6 times

- **Option to Reroll**
  - Some DMs allow rerolling bad results
  - Toggle: "Allow reroll if total is below 70" (optional rule)
  - "Reroll All" button if total too low

#### Results Display
- Six rolled scores shown (e.g., 16, 14, 13, 12, 11, 9)
- Summary statistics:
  - Total: XX
  - Average: X.X
  - Highest: XX
  - Lowest: XX
- Comparison to Standard Array shown

#### Assignment Interface
- Same as Standard Array
- Drag/drop or click to assign rolled scores to abilities
- Background bonuses applied
- Real-time impact display

---

### Manual Entry Option
- "Enter Custom Scores" (for DMs with house rules)
- Direct number input for each ability
- Validation: Typically 3-20 range
- Warning if scores unusual

### Educational Tooltips
Throughout this screen:
- Hover over ability name → What it does, which classes need it
- Hover over modifier → How modifiers are calculated
- Hover over background bonus → Why you got this bonus
- Icons with "?" for deeper explanations

### Bottom Action Bar
- Validation:
  - ✓ All ability scores assigned
  - ✓ Background bonuses applied
  - ✓ Modifiers calculated
- "Continue to Alignment" button
- "Change Method" button (restart this step)
- Character sheet preview (shows all current stats)

### API Calls
```
GET /api/characters/:id
- Returns: Current character state with class and background

PUT /api/characters/:id/ability-scores
- Payload: { 
    method: "standard_array" | "point_buy" | "roll" | "manual",
    strength: 15,
    dexterity: 14,
    constitution: 13,
    intelligence: 12,
    wisdom: 10,
    charisma: 8,
    roll_results: [16,14,13,12,11,9] // if rolled
  }
- Returns: Updated character with all derived stats calculated
  - HP, AC, initiative, save bonuses, skill bonuses, etc.

POST /api/dice/roll
- Payload: { dice: "4d6dl1", count: 6 } // drop lowest
- Returns: { rolls: [[5,3,4,2], [6,5,4,3], ...], totals: [12,15,...] }
- Used for server-validated rolling (anti-cheat)
```

### Data Validation
- Ability scores reasonable (3-20 base, up to 22 with bonuses)
- Point buy: Cannot exceed 27 points or go below 8/above 15
- All six abilities must have values
- Modifiers correctly calculated: (Score - 10) ÷ 2, rounded down

---

## Step 4: Choose Your Alignment

### Page Header
- Progress indicator: "Step 4 of 6: Choose Your Alignment"
- Note: "This is optional—some games don't use alignment"

### UI Components

#### Introduction Panel
- Brief explanation of alignment system
- "What is alignment?" expandable section
  - Explains two axes: Lawful-Chaotic, Good-Evil
  - Notes that alignment is descriptive, not prescriptive
  - Can change during campaign
- "Skip this step" option (sets to "Unaligned" or "No Alignment")

#### Alignment Grid (3x3 Visual)
Interactive grid layout:

```
┌──────────────┬──────────────┬──────────────┐
│ Lawful Good  │ Neutral Good │ Chaotic Good │
│              │              │              │
│   [Icon]     │   [Icon]     │   [Icon]     │
├──────────────┼──────────────┼──────────────┤
│ Lawful       │ True         │ Chaotic      │
│ Neutral      │ Neutral      │ Neutral      │
│   [Icon]     │   [Icon]     │   [Icon]     │
├──────────────┼──────────────┼──────────────┤
│ Lawful Evil  │ Neutral Evil │ Chaotic Evil │
│              │              │              │
│   [Icon]     │   [Icon]     │   [Icon]     │
└──────────────┴──────────────┴──────────────┘
```

Each cell is a card with:
- Alignment name
- Icon/symbol representing the alignment
- One-sentence description
- "Learn More" button

#### Alignment Detail View
When user clicks a cell or "Learn More":

**Description Tab**
- Full explanation of what this alignment means
- Moral and ethical perspective
- How characters with this alignment typically act

**Examples Tab**
- Famous D&D characters with this alignment
- Pop culture character examples
- Example behaviors and decisions

**Considerations Tab**
- How this fits with your class
- Party dynamics considerations
- Common misconceptions

#### Character Alignment Influences
Optional: Show how class/background might influence alignment
- "Many [Your Class] tend toward [Alignment]"
- "Your background suggests [Alignment traits]"
- Not prescriptive, just suggestions

### Selection Interaction
1. User explores alignment options
2. Clicks on alignment card
3. Reviews details
4. Clicks "Choose [Alignment]" button
5. Confirmation
6. Option to write alignment notes: "What does this mean for [Character Name]?"

### Optional Depth: Alignment Nuances
- Slider between Lawful-Chaotic (1-9 scale)
- Slider between Good-Evil (1-9 scale)
- Allows for "Lawful Good leaning Neutral"
- Visual position on 2D grid

### Bottom Action Bar
- Selected alignment displayed
- "Continue to Details" button
- "Skip Alignment" button
- Can change anytime

### API Calls
```
PUT /api/characters/:id/alignment
- Payload: { 
    alignment: "lawful_good",
    alignment_notes: "Believes in justice..."
  }
- Returns: Updated character
```

### Note on Alignment
Some modern campaigns de-emphasize alignment, so:
- Clear messaging that this is optional
- Can be changed anytime
- Doesn't affect mechanics (in 2024 rules)
- Focus is on personality, not alignment

---

## Step 5: Choose Equipment & Spells

### Page Header
- Progress indicator: "Step 5 of 6: Equip Your Character"
- Tabs: "Equipment" | "Spells" (if spellcaster) | "Feats & Features"

---

## Step 5A: Equipment

### Starting Equipment Summary
Top of page shows what character already has from:
- Class starting equipment (chosen in Step 1)
- Background equipment (or gold)
- Total starting gold

### UI Components

#### Equipment Slots Visualization
Paper doll or equipment slot display:
- **Armor Slot**: Head, Body, Shield
- **Weapon Slots**: Main Hand, Off Hand
- **Accessories**: Ring slots, Amulet, Belt, Boots, Cloak
- **Containers**: Backpack contents

Each slot shows:
- What's equipped (if anything)
- Mechanical benefit (AC for armor, damage for weapons)
- Weight
- "Change" or "Equip" button

#### Equipment Inventory Panel
List/grid view of all owned equipment:
- **Worn/Equipped** (green badge)
- **In Backpack** (with encumbrance calculation)
- **Can't Use** (if not proficient, red badge)

Each item shows:
- Name and icon
- Item type
- Weight
- Properties/effects
- "Equip" / "Unequip" / "Drop" buttons
- "Details" to see full description

#### Equipment Details Modal
When clicking on item:
- Full item description
- Mechanical stats
- Properties explained (Versatile, Finesse, etc.)
- If weapon: Attack bonus and damage calculated with character stats
- If armor: AC calculation shown
- Proficiency check (character can/can't use effectively)

#### Armor Selection & AC Calculation
If multiple armor options:
- **AC Calculator Widget** (always visible)
  - Shows current AC
  - Formula displayed: Base AC + Dex mod + shield
  - Different armors show "AC would be X if equipped"
  - Recommendations based on class and Dexterity

- Armor comparison:
  - AC provided
  - Strength requirement
  - Stealth disadvantage (yes/no)
  - Weight
  - "Best for you" badge on optimal choice

#### Weapon Selection
If multiple weapon options:

**Weapon Comparison Table**
- Name
- Damage (dice + modifier calculated)
- Attack bonus (calculated)
- Properties
- Mastery property (if applicable)
- Two-handed vs Versatile vs One-handed
- Range (for ranged weapons)

**Dual Wielding Setup**
- If character has weapons with Light property:
  - Toggle: "Enable dual wielding"
  - Main hand and off-hand selection
  - Shows both attack options

**Weapon Mastery Assignment** (if class feature)
- Reminder of which weapons mastered
- Visual indicator on mastered weapons
- "You can use [Property] with this weapon"

#### Shopping Interface (Optional - if given gold)
If background gave gold instead of equipment:
- "Visit the Market" button
- Shop interface:
  - Categories: Armor, Weapons, Adventuring Gear, Tools
  - Filter by: Price, Type, Usable by me
  - Sort by: Price, Name, Weight
  - Search bar
  - Gold remaining counter
  - Shopping cart
  - "Buy" buttons
- Starting equipment suggestions for class

#### Backpack & Encumbrance
- Carrying capacity calculated (Strength × 15)
- Current weight / Max weight
- Visual weight bar (green → yellow → red)
- Warning if encumbered
- "Add to Backpack" for items not worn
- Category organization (Weapons, Armor, Tools, Consumables, Misc)

### Bottom Section
- **Summary Cards**:
  - AC: X
  - Main weapon attack: +X, damage: XdX+X
  - Off-hand weapon (if any)
  - Carrying: X/Y lbs

### API Calls
```
GET /api/characters/:id/starting-equipment
- Returns: Items from class and background

GET /api/equipment
- Query params: ?category=armor&proficient_for_class=X
- Returns: Filtered equipment list with full stats

GET /api/equipment/:id
- Returns: Full item details

PUT /api/characters/:id/equipment
- Payload: { equipped_items: [], inventory_items: [], gold: X }
- Returns: Updated character with AC and encumbrance calculated

POST /api/characters/:id/equipment/:item_id/equip
- Returns: Updated equipped status

GET /api/equipment/shop
- Returns: Available starting equipment for purchase
```

---

## Step 5B: Spells (For Spellcasters Only)

### Display Condition
Only shows if class can cast spells

### UI Components

#### Spellcasting Summary Panel
- **Spellcasting Ability**: [Ability] (from class)
- **Spell Save DC**: Calculated and displayed
- **Spell Attack Bonus**: Calculated and displayed
- **Spell Slots**: Table by level
  - Level 1: X slots
  - Higher levels (grayed out, "Available at level X")
- **Spells Known/Prepared**: Current / Maximum

#### Cantrip Selection (if applicable)
- "Select [X] Cantrips" header with counter
- Spell grid layout with cards

**Each Cantrip Card Shows**:
- Spell name
- School icon and badge
- Casting time
- Range
- Duration
- Components (V, S, M) with icons
- Damage or effect summary
- "Select" button or checkbox
- "View Details" button

**Spell Details Modal**:
- Full spell description
- At higher levels scaling
- Mechanical breakdown
- Use cases and tips
- Components details

#### 1st-Level Spell Selection

**For "Spells Known" Casters (Bard, Sorcerer, Warlock)**:
- "Choose [X] 1st-level spells"
- Same grid interface as cantrips
- Locked-in choices (can't change easily)

**For "Prepared Spells" Casters (Cleric, Druid, Paladin, Wizard)**:
- "Choose [X] prepared spells from your class list"
- Note: "You can change these after a long rest"
- Same grid interface
- More flexible messaging

#### Spell Filtering & Search
- **Search bar**: Search by name or effect
- **Filters**:
  - School of Magic (Abjuration, Evocation, etc.)
  - Casting Time (Action, Bonus Action, Reaction, Ritual)
  - Range (Self, Touch, 30ft, etc.)
  - Concentration (Yes/No)
  - Damage Type (Fire, Cold, etc.)
  - Ritual (Yes/No)
- **Sort by**:
  - Alphabetical
  - School
  - Range
  - Most popular (based on community data)

#### Spell List View Options
- **Grid view**: Cards with images
- **List view**: Compact rows
- **Comparison view**: Side-by-side up to 3 spells

#### Recommended Spells
- "Essential [Class] Spells" section
- Tagged by utility:
  - Combat - Red badge
  - Healing - Green badge
  - Utility - Blue badge
  - Control - Purple badge
  - Buff - Yellow badge

#### Spell Book / Prepared Spell Interface (Class-Specific)

**Wizard Special Case**:
- "Spellbook" tab separate from "Prepared Spells"
- Starts with 6 1st-level spells in spellbook
- Can prepare [Intelligence mod + Wizard level] spells
- Two-step process:
  1. Choose spells for spellbook
  2. Choose which to prepare (subset of spellbook)

**Cleric/Druid**:
- Have access to full class list
- Choose which to prepare
- Note: "You have access to all [Class] spells and can change prepared spells after a long rest"

#### Spell Slots Reminder
- Visual representation of spell slots
- "You have X 1st-level spell slots"
- "You can cast any prepared spell using these slots"
- Link to "How spell slots work" tutorial

### API Calls
```
GET /api/spells?class_id=X&level=0,1
- Returns: Available spells for class at current level
- Includes: All spell data for display

GET /api/spells/:id
- Returns: Full spell details

PUT /api/characters/:id/spells
- Payload: { 
    cantrips: [spell_ids],
    known_spells: [spell_ids],
    prepared_spells: [spell_ids],
    spellbook: [spell_ids] // for wizards
  }
- Returns: Updated character with spells

GET /api/spells/recommended?class_id=X&level=1
- Returns: Curated list of recommended spells with reasoning
```

---

## Step 5C: Review Feats & Features

### UI Components

#### Features Summary
Expandable list of all features character has:

**From Class**:
- Each level 1 feature displayed
  - Name
  - Description
  - Usage (Action type, uses per rest)
  - When you might use it

**From Background**:
- Origin Feat
  - Full description
  - Any choices made displayed

**From Species**:
- Each trait
  - Description
  - Mechanical effect

#### Interactive Feature Cards
Features that require tracking:
- **Second Wind** (Fighter)
  - Uses: 2 / 2
  - Recharge: Short Rest (1 use) or Long Rest (all uses)
- **Rage** (Barbarian)
  - Uses: X / X
  - Recharge: Long Rest
- **Ki Points** (Monk)
  - Current: X
- Any limited-use abilities

#### Feature Education
- Tooltips on how to use each feature
- "When should I use this?" suggestions
- Tactical tips

### Bottom Action Bar
- "All equipment selected" checklist
- If spellcaster: "All spells chosen" checklist
- "Continue to Character Details" button

---

## Step 6: Fill in Character Details

### Page Header
- Progress indicator: "Step 6 of 6: Bring Your Character to Life"
- Note: "These details add personality but don't affect game mechanics"

### UI Components

#### Essential Details Section

**Character Name** (Required)
- Text input (large, prominent)
- "Random Name Generator" button
  - Generates appropriate names for species
  - Can filter by culture/region
  - Show multiple options
- Character name appears in header of all subsequent pages

**Physical Characteristics**
- Age (number input or dropdown ranges)
- Height (dropdown: Short/Average/Tall for species + custom inches)
- Weight (dropdown: Light/Average/Heavy for species + custom lbs)
- Eyes (color picker or text input)
- Skin (color picker or text input)
- Hair (color picker or text input)

**Pronouns** (Optional)
- Dropdown: He/Him, She/Her, They/Them, Custom
- Respectful representation

**Character Portrait** (Optional)
- Upload image option
- Choose from avatar library
- AI-generated portrait option (if available)
- Drag to reposition/zoom
- Default icon if none selected

#### Personality Section (Optional but Encouraged)

**Personality Traits**
- Text area with helpful prompts
- "What makes your character unique?"
- Examples shown as inspiration
- Suggested prompts based on background:
  - As a [Background], you might...
  - Your [Species] heritage means...

**Ideals**
- "What do you believe in?"
- Text area
- Examples: "Freedom is worth fighting for" or "Knowledge is power"

**Bonds**
- "Who or what matters most to you?"
- Text area
- Examples: "I owe my life to my mentor" or "I seek revenge against..."

**Flaws**
- "What weakness might get you in trouble?"
- Text area
- Examples: "I can't resist a good mystery" or "I'm too trusting"
- Note: "Flaws make characters interesting!"

#### Backstory Section

**Backstory Text Editor**
- Rich text editor
- "Write your character's story"
- Helpful prompts:
  - Where did you grow up?
  - What led you to become a [Class]?
  - Why did you leave your old life?
  - What are you seeking?
- Optional: Template/questionnaire mode
  - Answer 5-10 questions
  - Auto-generates backstory paragraph
- Character count (optional, some DMs prefer brief backgrounds)

**Background Connections** (Optional)
- "Connect with other party members"
- Fields to note:
  - How you know other PCs
  - Shared history
  - Why you adventure together
- Note: "Coordinate with your party!"

#### Additional Details

**Faith & Deity** (Optional)
- Particularly relevant for Clerics/Paladins
- Dropdown of deities by pantheon
- Custom deity option
- "No deity" option
- Description of what they represent

**Organizations & Affiliations**
- Text input for guilds, factions, families
- Tags for multiple organizations

**Goals & Motivations**
- Short-term goals
- Long-term goals
- What drives this character?

**Fears & Secrets**
- Optional private notes
- "Only you and your DM can see these"

### Visual Summary Panel (Right Side)
As user fills in details, character summary updates:
- Portrait/avatar
- Name, species, class display
- Quick stats display
- Personality snippet
- "This is [Character Name], a [Alignment] [Species] [Class]..."

### Character Voice (Optional)
- "How does your character sound?"
- Voice description text
- Common phrases or catchphrases
- Speech patterns

### Fun/Optional Fields
- **Favorite Food**
- **Hobby**
- **Quirk/Mannerism**
- **What does your character carry as a memento?**
- "These small details bring characters to life!"

### Bottom Action Bar
- "Character name required to continue"
- "Finish Character Creation" button (exciting, prominent)
- "Save Draft" button (auto-save happening throughout)

### API Calls
```
PUT /api/characters/:id/details
- Payload: {
    character_name: "Angriff",
    age: 45,
    height: "4'8\"",
    weight: 180,
    eyes: "Brown",
    skin: "Ruddy",
    hair: "Black with grey",
    pronouns: "He/Him",
    portrait_url: "...",
    personality_traits: "...",
    ideals: "...",
    bonds: "...",
    flaws: "...",
    backstory: "...",
    deity: "...",
    organizations: ["..."],
    goals: "...",
    additional_notes: {...}
  }
- Returns: Completed character

POST /api/characters/:id/portrait
- Payload: FormData with image file
- Returns: { portrait_url: "..." }

GET /api/names/generate?species=dwarf&gender=male
- Returns: { names: ["Thorin", "Balin", ...] }
```

---

## Character Complete: Review & Confirmation

### Page Layout
Full character sheet preview with celebration!

### UI Components

#### Celebration Header
- "🎉 Character Created Successfully!"
- Confetti animation or celebratory graphic
- "[Character Name] is ready for adventure!"

#### Character Sheet Preview
Full, formatted character sheet showing:

**Header Section**
- Character portrait
- Name, level, class, species, background
- Player name (if applicable)
- Experience points: 0 / 300 (for level 2)

**Ability Scores** (prominent display)
- All six abilities with scores and modifiers in boxes
- Saving throw proficiencies marked

**Core Stats**
- Armor Class (large, bold)
- Initiative
- Speed
- Hit Points (current/max)
- Hit Dice available
- Proficiency Bonus

**Skills List**
- All skills with checkboxes for proficiency
- Calculated bonuses shown
- Expertise marked (if any)

**Combat Section**
- Attacks list:
  - Weapon name
  - Attack bonus
  - Damage + type
  - Properties
- Weapon masteries noted

**Features & Traits**
- Expandable sections for:
  - Class features
  - Species traits
  - Feats
  - Background benefits
- Usage tracking for limited abilities

**Proficiencies**
- Armor
- Weapons
- Tools
- Languages
- Saving Throws

**Equipment**
- Worn armor
- Equipped weapons
- Backpack contents
- Total weight
- Currency

**Spells** (if spellcaster)
- Spell save DC
- Spell attack bonus
- Spell slots by level
- Cantrips list
- Known/prepared spells by level

**Personality**
- Traits, ideals, bonds, flaws
- Backstory summary

### Action Options

**Primary Actions**
- "Download Character Sheet" button
  - PDF format
  - Multiple sheet layouts (official, custom, compact)
  - Print-optimized
  
- "Save to My Characters" button
  - Saves to account
  - Confirmation: "Saved!"

**Sharing Options**
- "Share with DM" button
  - Generate shareable link
  - QR code option
  - Email directly
  
- "Export Data" button
  - JSON format
  - Compatible with VTTs (Fantasy Grounds, Roll20, etc.)
  - Foundry VTT format option

**Editing Options**
- "Make Changes" button
  - Dropdown to jump to specific step
  - Edit without losing progress
  
- "Create Similar Character" button
  - Duplicates and allows variations
  - "What if this character was a Wizard instead?"

**Companion Actions**
- "Create Another Character" button
  - Starts fresh
  - Option to use same campaign/settings

- "Level Up" button (future feature)
  - Grayed out: "Available at 300 XP"

### Validation & Warnings
Before finalizing:
- Check for any incomplete selections
- Warning if character seems unusual:
  - "Your primary ability is low—are you sure?"
  - "You're not wearing armor—is this intentional?"
- These are suggestions, not blockers

### DM Notes Section (Optional)
If creating character for a campaign:
- Campaign name shown
- DM's house rules applied
- Special restrictions noted
- "Your DM will review this character"

### Tutorial/Help Offer
- "New to D&D?" callout
- Link to "How to Play Your [Class]" guide
- "Next Steps" checklist:
  - ✓ Character created
  - ☐ Coordinate with party
  - ☐ Discuss backstory with DM
  - ☐ Prepare for Session 0/1

### API Calls
```
GET /api/characters/:id/sheet
- Returns: Complete formatted character data

POST /api/characters/:id/finalize
- Marks character as complete
- Returns: { status: "complete", share_code: "ABC123" }

GET /api/characters/:id/export?format=pdf
- Returns: PDF file download

GET /api/characters/:id/export?format=json
- Returns: JSON character data

GET /api/characters/:id/export?format=foundry
- Returns: Foundry VTT compatible format

POST /api/characters/:id/share
- Payload: { recipient_email: "dm@example.com" }
- Returns: { share_link: "..." }

POST /api/characters/:id/duplicate
- Returns: New character_id with copied data
```

---

## Additional App Features

### Navigation Features Throughout

#### Persistent Elements

**Top Navigation Bar** (all pages)
- App logo (home link)
- Current step indicator
- Character name display (once entered)
- Progress saved indicator (cloud sync icon)
- Help button (context-sensitive)
- Save & Exit button
- Settings dropdown

**Character Summary Widget** (sidebar or collapsible)
- Always shows current selections
- Quick stats at a glance
- Click to jump to any completed step
- Reminds user of choices made

**Bottom Action Bar** (all pages)
- Back button (with confirmation if changes)
- Continue/Next button (disabled until requirements met)
- Character sheet preview drawer trigger
- Requirements checklist

#### Character Sheet Live Preview
Accessible from any step:
- Drawer slides in from right
- Shows current character sheet in real-time
- All stats calculated
- Updates as user makes choices
- "See how your choices affect your character!"

### Help System

**Context-Sensitive Help**
- "?" icons throughout
- Hover tooltips
- Expandable help panels
- "Learn more about [Topic]" links

**Glossary**
- Searchable term definitions
- Accessible from any page
- Categories: Rules, Classes, Combat, Spells, etc.

**Video Tutorials**
- "Watch How" video icons
- Short clips explaining complex choices
- "How to choose a class" (2 min video)
- "Understanding ability scores" (3 min video)

**Guided Tour**
- First-time user walkthrough
- Highlights key features
- Can be replayed anytime

### Settings & Preferences

**Accessibility Options**
- High contrast mode
- Font size adjustment
- Dyslexia-friendly font option
- Screen reader optimization
- Keyboard navigation support
- Reduced motion option

**User Preferences**
- Tooltips: Beginner / Standard / Expert / Off
- Metric or Imperial measurements
- Dice rolling: Manual, automatic, hybrid
- Auto-save frequency
- Default character sheet layout

**Campaign Settings**
- Associate character with campaign
- Apply campaign-specific house rules
- Starting level (if not 1)
- Allowed sources (PHB only, all official, homebrew)
- Point buy vs Standard Array defaults

### Data Management

**Auto-Save**
- Saves every 30 seconds
- "All changes saved" indicator
- Recovers from browser crash
- Persists across devices (if logged in)

**Version History**
- "View previous versions"
- Restore earlier state if needed
- "Undo last 5 changes" option

**Character List Management**
- Filter by: Campaign, Class, Level, Date
- Search by name
- Archive old characters
- Favorite/star characters
- Folders for organization

### Social Features

**Share Builds**
- "Share this build" button
- Public character gallery (opt-in)
- Upvote/comment on popular builds
- "Copy build" to create similar character

**Party Coordination**
- Link characters in same campaign
- See party composition
- Identify role gaps ("Your party needs a healer")
- Share resources (like party inventory)

**Community**
- Character build guides
- Class discussion forums
- "Rate my character" feature
- Build recommendations from community

---

## Mobile Responsiveness

### Mobile Adaptations

**Touch Optimizations**
- Larger tap targets (min 44x44px)
- Swipe gestures for navigation
- Drag & drop alternatives (tap to select)
- Bottom sheet modals instead of sidebars

**Simplified Layouts**
- Single column layouts
- Collapsible sections
- Tabbed interfaces over side-by-side
- Sticky headers and action buttons

**Mobile-Specific Features**
- Dice rolling with device shake
- Camera for character portrait
- Save to homescreen as PWA
- Offline mode for viewing characters

**Performance**
- Lazy loading of images
- Reduced animations on mobile
- Compressed assets
- Efficient data fetching

---

## Error Handling & Edge Cases

### Error States

**Network Errors**
- "Can't connect to server" message
- Retry button
- Offline mode indicator
- Queued changes sync when reconnected

**Validation Errors**
- Inline error messages
- Red highlights on invalid fields
- Clear explanation of what's wrong
- Suggestion for how to fix

**Data Conflicts**
- If editing same character on multiple devices
- "Conflict detected" modal
- Choose which version to keep
- Merge changes option

### Edge Cases

**Browser Compatibility**
- Graceful degradation for older browsers
- Feature detection
- Polyfills for critical features
- "Upgrade browser" suggestion if needed

**Incomplete Sessions**
- "Resume where you left off"
- Draft characters clearly marked
- Auto-delete abandoned drafts after 30 days
- Export draft option

**Invalid Combinations**
- Prevent impossible builds
- Warning for suboptimal choices
- "Are you sure?" confirmations
- Override option for experienced users

---

## Analytics & Tracking (for Product Improvement)

### User Behavior Tracking
- Time spent on each step
- Most common class/background/species combinations
- Drop-off points in creation flow
- Feature usage (tooltips, help, recommendations)
- Error frequency and types

### A/B Testing Capabilities
- Test different UI layouts
- Compare drag-drop vs click-to-select
- Test recommendation algorithms
- Measure completion rates

### Performance Monitoring
- API response times
- Page load times
- Error rates
- Browser/device usage statistics

---

## Security & Privacy

### Data Protection
- Encrypted data transmission (HTTPS)
- Secure authentication
- Password requirements
- Session management

### Privacy Controls
- Character visibility settings (private/public)
- Data export anytime
- Account deletion option
- GDPR compliance

### Content Moderation
- Report inappropriate content
- Profanity filters (optional)
- Community guidelines
- Admin review system

---

## Future Enhancements

### Planned Features
- **Level Up Wizard**: Guide character advancement
- **Multi-classing**: Advanced character building
- **Magic Item Integration**: Add and track magic items
- **Campaign Management**: DM tools integration
- **Character Journals**: Session notes and character development
- **AI Assistant**: "Help me choose" smart recommendations
- **Voice Character Creation**: Verbal input option
- **Collaborative Building**: Build character with DM in real-time
- **Character Templates**: Quick start pre-built characters
- **Homebrew Content**: Custom classes, species, backgrounds
- **VTT Integration**: Direct export to Roll20, Foundry, etc.

---

## Summary: Complete API Requirements

### Core APIs Needed

**Authentication**
```
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET /api/auth/verify
```

**Character Management**
```
GET /api/characters
POST /api/characters
GET /api/characters/:id
PUT /api/characters/:id
DELETE /api/characters/:id
POST /api/characters/:id/duplicate
POST /api/characters/:id/finalize
GET /api/characters/:id/sheet
GET /api/characters/:id/export
```

**Game Content**
```
GET /api/classes
GET /api/classes/:id
GET /api/backgrounds
GET /api/backgrounds/:id
GET /api/species
GET /api/species/:id
GET /api/feats
GET /api/skills
GET /api/equipment
GET /api/weapons
GET /api/armor
GET /api/spells
GET /api/languages
```

**Character Building**
```
PUT /api/characters/:id/class
PUT /api/characters/:id/background
PUT /api/characters/:id/species
PUT /api/characters/:id/ability-scores
PUT /api/characters/:id/alignment
PUT /api/characters/:id/equipment
PUT /api/characters/:id/spells
PUT /api/characters/:id/details
```

**Utilities**
```
POST /api/dice/roll
GET /api/names/generate
POST /api/characters/:id/portrait
GET /api/recommendations
POST /api/validation
```

**Social**
```
POST /api/characters/:id/share
GET /api/characters/public
POST /api/characters/:id/favorite
```

---

## Conclusion

This user journey provides a comprehensive, step-by-step experience for creating a D&D character. The design prioritizes:

1. **Progressive Disclosure**: Information revealed when needed
2. **Education**: Help for new players without overwhelming experienced ones
3. **Flexibility**: Multiple methods for each choice (drag-drop, click, manual)
4. **Real-time Feedback**: Character sheet updates as choices made
5. **Validation**: Prevents impossible builds while allowing creativity
6. **Accessibility**: Usable by players of all experience levels and abilities
7. **Mobile-First**: Works seamlessly across all devices

The application guides users through complex D&D rules while maintaining excitement and engagement throughout the character creation process.