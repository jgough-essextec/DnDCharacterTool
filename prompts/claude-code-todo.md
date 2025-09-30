# D&D Character Creator - Claude Code Development Tasks

## Project Overview
Build a full-stack D&D character creation application using Django, PostgreSQL, and deploy as a serverless application on AWS using Zappa.

**Tech Stack:**
- Backend: Django 5.x + Django REST Framework
- Database: PostgreSQL (AWS RDS)
- Deployment: Zappa (AWS Lambda + API Gateway)
- Frontend: Django Templates + HTMX + Alpine.js (or separate React SPA)
- Storage: AWS S3 (for character portraits, static files)
- Auth: Django authentication + JWT for API

---

## Phase 1: Project Setup & Infrastructure

### 1.1 Initial Django Project Setup
- [ ] Create new Django project: `django-admin startproject dnd_character_creator`
- [ ] Set up virtual environment with Python 3.11+
- [ ] Create `requirements.txt` with core dependencies:
  - Django==5.0.x
  - djangorestframework==3.14.x
  - psycopg2-binary==2.9.x
  - django-cors-headers
  - djangorestframework-simplejwt
  - python-dotenv
  - zappa==0.59.x
  - boto3 (for AWS services)
  - Pillow (for image handling)
  - django-storages (for S3 integration)
- [ ] Create `.env.example` file for environment variables
- [ ] Set up `.gitignore` for Python/Django projects
- [ ] Initialize git repository

### 1.2 Database Configuration
- [ ] Configure PostgreSQL settings in `settings.py`
- [ ] Create separate settings files:
  - `settings/base.py` - Common settings
  - `settings/local.py` - Local development
  - `settings/production.py` - Production/AWS settings
- [ ] Set up environment variable handling with `python-dotenv`
- [ ] Create local PostgreSQL database for development
- [ ] Test database connection

### 1.3 AWS Infrastructure Setup
- [ ] Create AWS account (if needed) and configure AWS CLI
- [ ] Set up IAM user for Zappa with required permissions:
  - Lambda full access
  - API Gateway full access
  - CloudFormation full access
  - S3 full access
  - CloudWatch Logs
  - IAM role creation
  - VPC access (for RDS)
- [ ] Create S3 bucket for Zappa deployments: `dnd-creator-zappa-deployments`
- [ ] Create S3 bucket for media files: `dnd-creator-media`
- [ ] Set up RDS PostgreSQL instance:
  - Choose appropriate instance size (start with db.t3.micro)
  - Configure security groups for Lambda access
  - Enable VPC access
  - Set up database credentials in AWS Secrets Manager
- [ ] Create VPC configuration for Lambda to access RDS
- [ ] Configure S3 bucket policies for public read on static files

### 1.4 Zappa Configuration
- [ ] Install Zappa: `pip install zappa`
- [ ] Initialize Zappa: `zappa init`
- [ ] Configure `zappa_settings.json`:
  ```json
  {
    "dev": {
      "django_settings": "dnd_character_creator.settings.production",
      "s3_bucket": "dnd-creator-zappa-deployments",
      "aws_region": "us-east-1",
      "runtime": "python3.11",
      "vpc_config": {
        "SubnetIds": ["subnet-xxxxx"],
        "SecurityGroupIds": ["sg-xxxxx"]
      },
      "environment_variables": {
        "DB_NAME": "dnd_creator",
        "DB_HOST": "xxx.rds.amazonaws.com"
      },
      "memory_size": 512,
      "timeout": 30
    },
    "production": {
      // Similar config with production values
    }
  }
  ```
- [ ] Test initial Zappa deployment: `zappa deploy dev`
- [ ] Set up custom domain (optional) with API Gateway
- [ ] Configure CloudWatch logging

---

## Phase 2: Core Django Apps & Models

### 2.1 Create Django Apps
- [ ] Create `core` app: `python manage.py startapp core`
- [ ] Create `characters` app: `python manage.py startapp characters`
- [ ] Create `game_content` app: `python manage.py startapp game_content`
- [ ] Create `users` app: `python manage.py startapp users` (custom user model)
- [ ] Register all apps in `INSTALLED_APPS`

### 2.2 User Management App
- [ ] Create custom User model in `users/models.py`
  - Extend AbstractUser
  - Add fields: profile_picture, bio, created_at, updated_at
- [ ] Create User serializers (DRF)
- [ ] Implement authentication endpoints:
  - POST /api/auth/register
  - POST /api/auth/login (JWT)
  - POST /api/auth/logout
  - GET /api/auth/verify
  - POST /api/auth/refresh (token refresh)
- [ ] Create user profile views and endpoints
- [ ] Add password reset functionality
- [ ] Implement email verification (optional)

### 2.3 Game Content Models (`game_content` app)

#### Classes
- [ ] Create `Class` model:
  - Fields: name, description, primary_ability, hit_die, difficulty
  - JSON fields: armor_proficiencies, weapon_proficiencies, saving_throw_proficiencies
- [ ] Create `ClassFeature` model:
  - ForeignKey to Class
  - Fields: name, level_acquired, description, feature_type, uses_per_rest
  - JSON field: choice_options
- [ ] Create `Subclass` model:
  - ForeignKey to Class
  - Fields: name, description, level_available
  - ManyToMany to ClassFeature

#### Backgrounds
- [ ] Create `Background` model:
  - Fields: name, description, starting_gold
  - JSON field: ability_score_increases
  - ForeignKey to Feat (origin_feat)
  - JSON fields: skill_proficiencies, tool_proficiencies, equipment_options

#### Species
- [ ] Create `Species` model:
  - Fields: name, description, size, speed, darkvision_range
  - JSON field: languages
- [ ] Create `SpeciesTrait` model:
  - ForeignKey to Species
  - Fields: name, description, trait_type
  - JSON field: mechanical_effect

#### Feats
- [ ] Create `Feat` model:
  - Fields: name, feat_type (origin/general/fighting_style), description, repeatable
  - JSON fields: prerequisites, ability_score_increase, benefits

#### Skills & Abilities
- [ ] Create `Skill` model:
  - Fields: name, associated_ability, description
- [ ] Create ability choices (enum or choices field)
  - STR, DEX, CON, INT, WIS, CHA

#### Equipment
- [ ] Create `Equipment` model:
  - Fields: name, equipment_type, cost_gp, weight, description
  - JSON field: properties
- [ ] Create `Weapon` model (inherits/extends Equipment):
  - Fields: weapon_category, damage_dice, damage_type, mastery_property, range
  - JSON field: properties
- [ ] Create `Armor` model (inherits/extends Equipment):
  - Fields: armor_type, base_ac, dex_bonus_limit, strength_requirement, stealth_disadvantage

#### Spells
- [ ] Create `Spell` model:
  - Fields: name, spell_level, school, casting_time, range, duration, concentration
  - Fields: components_v, components_s, components_m, material_components
  - Text fields: description, higher_level_description
  - ManyToMany to Class (available_to_classes)

#### Languages
- [ ] Create `Language` model:
  - Fields: name, script, typical_speakers, rarity

### 2.4 Character Models (`characters` app)

#### Main Character Model
- [ ] Create `Character` model:
  - ForeignKey to User
  - ForeignKey to Class, Subclass (nullable), Background, Species
  - Fields: character_name, level, experience_points, alignment
  - Fields: current_hp, max_hp, temporary_hp, armor_class, initiative, speed
  - Fields: proficiency_bonus, inspiration
  - JSON field: additional_notes
  - Fields: created_date, last_modified_date, is_complete
  - Character state: draft, complete, archived

#### Character Abilities
- [ ] Create `CharacterAbilities` model (OneToOne with Character):
  - Fields: strength_score, dexterity_score, constitution_score
  - Fields: intelligence_score, wisdom_score, charisma_score
  - Properties to calculate modifiers

#### Character Proficiencies
- [ ] Create `CharacterSkill` model:
  - ForeignKey to Character, Skill
  - Field: proficiency_type (none/proficient/expertise)
- [ ] Create `CharacterSavingThrow` model:
  - ForeignKey to Character
  - Fields: ability_name, is_proficient
- [ ] Create `CharacterProficiency` model (generic):
  - ForeignKey to Character
  - Fields: proficiency_type (armor/weapon/tool), proficiency_name

#### Character Equipment
- [ ] Create `CharacterEquipment` model:
  - ForeignKey to Character, Equipment
  - Fields: quantity, equipped, attuned (for magic items)

#### Character Spells
- [ ] Create `CharacterSpell` model:
  - ForeignKey to Character, Spell
  - Fields: always_prepared, prepared

#### Character Features
- [ ] Create `CharacterFeature` model:
  - ForeignKey to Character, ClassFeature
  - Fields: uses_remaining
  - JSON field: choice_made

#### Character Feats
- [ ] Create `CharacterFeat` model:
  - ForeignKey to Character, Feat
  - Fields: source (background/class/ASI)
  - JSON field: choice_made

#### Character Languages
- [ ] Create `CharacterLanguage` model:
  - ManyToMany between Character and Language

#### Character Details
- [ ] Create `CharacterDetails` model (OneToOne with Character):
  - Fields: age, height, weight, eyes, skin, hair, pronouns
  - Field: portrait_url (S3 link)
  - Text fields: personality_traits, ideals, bonds, flaws, backstory, notes

### 2.5 Database Migrations
- [ ] Create initial migrations: `python manage.py makemigrations`
- [ ] Review migration files for correctness
- [ ] Apply migrations: `python manage.py migrate`
- [ ] Create database indexes for commonly queried fields:
  - Character.user_id
  - Character.is_complete
  - CharacterSpell lookup fields
  - Equipment name
  - Spell level and class availability

---

## Phase 3: Django Admin & Data Population

### 3.1 Django Admin Configuration
- [ ] Register all models in admin interface
- [ ] Customize admin displays with `list_display`, `list_filter`, `search_fields`
- [ ] Create custom admin actions (bulk approve, export, etc.)
- [ ] Set up inline admin for related models:
  - ClassFeatures inline with Class
  - SpeciesTraits inline with Species
  - CharacterEquipment inline with Character
- [ ] Add admin dashboard customization (optional)

### 3.2 Data Import/Fixtures
- [ ] Create management command for importing D&D data:
  - `python manage.py import_dnd_data`
- [ ] Import Classes (all 13 classes from 2024 PHB):
  - Barbarian, Bard, Cleric, Druid, Fighter, Monk
  - Paladin, Ranger, Rogue, Sorcerer, Warlock, Wizard, Artificer
- [ ] Import Class Features for each class at levels 1-20
- [ ] Import Subclasses for each class
- [ ] Import Backgrounds (16 from 2024 PHB):
  - Acolyte, Artisan, Charlatan, Criminal, Entertainer, Farmer
  - Guard, Guide, Hermit, Merchant, Noble, Sage
  - Sailor, Scribe, Soldier, Wayfarer
- [ ] Import Species (10+ from 2024 PHB):
  - Human, Elf, Dwarf, Halfling, Orc, Tiefling
  - Dragonborn, Gnome, Goliath, Aasimar
- [ ] Import all Species Traits
- [ ] Import Feats (Origin, General, Fighting Style)
- [ ] Import all 18 Skills
- [ ] Import Equipment (100+ items):
  - All weapons (simple and martial)
  - All armor types
  - Adventuring gear
  - Tools
- [ ] Import Spells (300+ spells):
  - All cantrips (level 0)
  - All 1st-9th level spells
  - Spell-to-Class associations
- [ ] Import Languages (Standard and Exotic)
- [ ] Create Django fixtures for consistent data:
  - `python manage.py dumpdata game_content > game_content_fixture.json`
- [ ] Add data validation management command

### 3.3 Data Seeding Scripts
- [ ] Create seed data for testing:
  - Sample users
  - Sample characters at various stages of completion
  - Edge case characters (multiclass, unusual builds)
- [ ] Create factory classes for testing (using Factory Boy):
  - UserFactory
  - CharacterFactory
  - ClassFactory, etc.

---

## Phase 4: REST API Development

### 4.1 DRF Setup
- [ ] Configure Django REST Framework in settings:
  - Add to INSTALLED_APPS
  - Configure DEFAULT_PERMISSION_CLASSES
  - Configure DEFAULT_AUTHENTICATION_CLASSES (JWT)
  - Set up pagination defaults
  - Configure throttling for API rate limiting
- [ ] Create base API router structure
- [ ] Set up API versioning (v1)
- [ ] Configure CORS headers for frontend

### 4.2 Serializers

#### Game Content Serializers
- [ ] Create `ClassSerializer` (summary and detail versions)
- [ ] Create `ClassFeatureSerializer`
- [ ] Create `SubclassSerializer`
- [ ] Create `BackgroundSerializer`
- [ ] Create `SpeciesSerializer` with nested `SpeciesTraitSerializer`
- [ ] Create `FeatSerializer`
- [ ] Create `SkillSerializer`
- [ ] Create `EquipmentSerializer`
- [ ] Create `WeaponSerializer` (extends EquipmentSerializer)
- [ ] Create `ArmorSerializer` (extends EquipmentSerializer)
- [ ] Create `SpellSerializer` (with filtering fields)
- [ ] Create `LanguageSerializer`

#### Character Serializers
- [ ] Create `CharacterListSerializer` (summary for list view)
- [ ] Create `CharacterDetailSerializer` (complete character)
- [ ] Create `CharacterCreateSerializer` (for initial creation)
- [ ] Create `CharacterAbilitiesSerializer`
- [ ] Create `CharacterSkillSerializer`
- [ ] Create `CharacterEquipmentSerializer`
- [ ] Create `CharacterSpellSerializer`
- [ ] Create `CharacterFeatureSerializer`
- [ ] Create `CharacterDetailsSerializer`
- [ ] Create `CharacterSheetSerializer` (formatted for display)

### 4.3 ViewSets & Views

#### Authentication Views
- [ ] Implement registration view
- [ ] Implement login view (return JWT tokens)
- [ ] Implement token refresh view
- [ ] Implement logout view (blacklist token)
- [ ] Implement user profile view

#### Game Content ViewSets
- [ ] Create `ClassViewSet` with list and detail actions
  - Add custom action for class comparison
  - Add filter by difficulty
- [ ] Create `BackgroundViewSet`
  - Add filter by recommended_for_class
- [ ] Create `SpeciesViewSet`
- [ ] Create `FeatViewSet`
  - Add filter by feat_type
- [ ] Create `SkillViewSet` (read-only)
- [ ] Create `EquipmentViewSet`
  - Add filters: category, proficient_for_class, price_range
  - Add search by name
- [ ] Create `WeaponViewSet`
  - Add filter by category (simple/martial)
- [ ] Create `ArmorViewSet`
  - Add filter by armor_type
- [ ] Create `SpellViewSet`
  - Add filters: class_id, level, school, concentration, ritual
  - Add search by name or description
  - Add pagination (important for 300+ spells)
- [ ] Create `LanguageViewSet` (read-only)

#### Character ViewSets
- [ ] Create `CharacterViewSet`:
  - List: GET /api/characters (user's characters only)
  - Create: POST /api/characters
  - Retrieve: GET /api/characters/:id
  - Update: PUT/PATCH /api/characters/:id
  - Delete: DELETE /api/characters/:id
  - Custom actions:
    - POST /api/characters/:id/duplicate
    - POST /api/characters/:id/finalize
    - GET /api/characters/:id/sheet
    - GET /api/characters/:id/export (PDF/JSON)
- [ ] Create character step-specific update views:
  - PUT /api/characters/:id/class
  - PUT /api/characters/:id/background
  - PUT /api/characters/:id/species
  - PUT /api/characters/:id/ability-scores
  - PUT /api/characters/:id/alignment
  - PUT /api/characters/:id/equipment
  - PUT /api/characters/:id/spells
  - PUT /api/characters/:id/details

#### Utility Views
- [ ] Create dice roller endpoint: POST /api/dice/roll
- [ ] Create name generator endpoint: GET /api/names/generate
- [ ] Create character portrait upload: POST /api/characters/:id/portrait
- [ ] Create recommendations endpoint: GET /api/recommendations
- [ ] Create validation endpoint: POST /api/validation

#### Social Features Views (Optional)
- [ ] Create character share endpoint: POST /api/characters/:id/share
- [ ] Create public characters endpoint: GET /api/characters/public
- [ ] Create favorite character endpoint: POST /api/characters/:id/favorite

### 4.4 Permissions & Authentication
- [ ] Create custom permission classes:
  - `IsOwnerOrReadOnly` - for characters
  - `IsAuthenticatedOrReadOnly` - for game content
- [ ] Apply permissions to all viewsets
- [ ] Test authentication flows
- [ ] Implement API key authentication for future mobile app (optional)

### 4.5 API Filtering, Searching, Pagination
- [ ] Install django-filter: `pip install django-filter`
- [ ] Configure DRF filters for each viewset
- [ ] Implement search functionality where needed
- [ ] Set up pagination:
  - PageNumberPagination for most endpoints
  - LimitOffsetPagination for spells
  - Default page size: 20

### 4.6 API Documentation
- [ ] Install drf-spectacular: `pip install drf-spectacular`
- [ ] Configure OpenAPI schema generation
- [ ] Add schema to URLs: `/api/schema/`
- [ ] Set up Swagger UI: `/api/docs/`
- [ ] Set up ReDoc: `/api/redoc/`
- [ ] Document all endpoints with docstrings
- [ ] Add example requests/responses

---

## Phase 5: Business Logic & Calculations

### 5.1 Character Calculation Service
- [ ] Create `CharacterCalculationService` class in `characters/services.py`
- [ ] Implement ability modifier calculation: `(score - 10) // 2`
- [ ] Implement proficiency bonus by level: `2 + ((level - 1) // 4)`
- [ ] Implement HP calculation:
  - Max HP at level 1: hit_die_max + CON_mod + species_bonus
- [ ] Implement AC calculation:
  - Base 10 + DEX_mod (unarmored)
  - Armor AC + min(DEX_mod, armor_dex_limit) + shield
- [ ] Implement Initiative calculation: DEX_mod
- [ ] Implement Skill bonus calculation: ability_mod + (prof_bonus if proficient)
- [ ] Implement Saving throw bonus: ability_mod + (prof_bonus if proficient)
- [ ] Implement Attack bonus calculation: ability_mod + prof_bonus (if proficient)
- [ ] Implement Spell save DC: 8 + prof_bonus + spellcasting_ability_mod
- [ ] Implement Spell attack bonus: prof_bonus + spellcasting_ability_mod
- [ ] Implement carrying capacity: STR_score × 15

### 5.2 Character Validation Service
- [ ] Create `CharacterValidationService` class
- [ ] Validate ability score ranges (3-20 typically)
- [ ] Validate point buy constraints (8-15 base, 27 points max)
- [ ] Validate spell selections:
  - Correct number of cantrips/spells for class/level
  - Spells are from class spell list
  - Prepared spells don't exceed limit
- [ ] Validate skill selections (exact count for class)
- [ ] Validate equipment proficiency
- [ ] Validate feat prerequisites
- [ ] Validate required choices are made for each step
- [ ] Return validation errors with helpful messages

### 5.3 Character Progression Service (Future)
- [ ] Create `CharacterProgressionService` class
- [ ] Implement XP to level calculation
- [ ] Implement level-up logic:
  - Increase level
  - Add new hit points
  - Add new features
  - Check for ASI/feat
  - Update spell slots
- [ ] Implement ASI (Ability Score Improvement) logic
- [ ] Implement multiclassing validation and application

### 5.4 Export Service
- [ ] Create `CharacterExportService` class
- [ ] Implement JSON export with full character data
- [ ] Implement PDF generation (use ReportLab or WeasyPrint):
  - Official D&D character sheet layout
  - Custom compact layout option
- [ ] Implement Foundry VTT export format
- [ ] Implement Roll20 export format (if possible)
- [ ] Store generated files temporarily in S3

### 5.5 Dice Rolling Service
- [ ] Create `DiceRollerService` class
- [ ] Implement dice notation parser (XdY+Z)
- [ ] Implement roll execution with results
- [ ] Implement 4d6 drop lowest (ability scores)
- [ ] Implement advantage/disadvantage (2d20, take higher/lower)
- [ ] Return detailed roll results (individual dice + total)
- [ ] Add optional server-side roll validation

### 5.6 Recommendation Service
- [ ] Create `RecommendationService` class
- [ ] Implement class recommendation based on playstyle quiz
- [ ] Implement background recommendation for chosen class
- [ ] Implement ability score assignment suggestion
- [ ] Implement spell recommendations (essential spells)
- [ ] Implement equipment recommendations
- [ ] Build recommendation logic based on class synergies

---

## Phase 6: Frontend Development

### 6.1 Frontend Architecture Decision
**Option A: Django Templates + HTMX + Alpine.js** (Recommended for faster deployment)
- Pros: Faster initial development, better SEO, simpler deployment
- Cons: Less interactive, harder to scale complex UI

**Option B: Separate React SPA**
- Pros: Highly interactive, modern UX, easier to add mobile app later
- Cons: More complex deployment, requires separate hosting/build

**Choose Option A for MVP, plan Option B for v2**

### 6.2 Frontend Setup (Django Templates approach)
- [ ] Install HTMX: Add CDN link or download locally
- [ ] Install Alpine.js: Add CDN link or download locally
- [ ] Install Tailwind CSS: Configure with Django
  - Use Tailwind CDN for MVP or set up with django-tailwind
- [ ] Set up static files structure:
  ```
  static/
    css/
    js/
    images/
    icons/
  ```
- [ ] Set up templates structure:
  ```
  templates/
    base.html
    components/
    pages/
      landing.html
      character_list.html
      step1_class.html
      step2_origin.html
      ... etc
  ```
- [ ] Configure static files for production (S3)
- [ ] Set up template context processors

### 6.3 Base Templates & Components
- [ ] Create `base.html` with:
  - Head with meta tags, CSS links
  - Navigation header
  - Main content block
  - Footer
  - JavaScript includes
- [ ] Create `components/navigation.html`
- [ ] Create `components/progress_indicator.html`
- [ ] Create `components/character_summary_widget.html`
- [ ] Create `components/tooltip.html`
- [ ] Create `components/modal.html`
- [ ] Create `components/loading_spinner.html`

### 6.4 Landing Page
- [ ] Create landing page template
- [ ] Display user's characters (if authenticated)
- [ ] Character card component with:
  - Portrait, name, class/species, level
  - Quick actions (edit, delete, view, duplicate)
- [ ] "Create New Character" CTA button
- [ ] Empty state for no characters
- [ ] Filter and sort controls
- [ ] Wire up HTMX for dynamic character loading

### 6.5 Step 1: Class Selection
- [ ] Create class selection page template
- [ ] Create class card component
- [ ] Create class details modal/panel
- [ ] Implement class comparison feature
- [ ] Create skill selection interface
- [ ] Create fighting style selection (for applicable classes)
- [ ] Create weapon mastery selection
- [ ] Create spell selection interface (for spellcasters)
- [ ] Wire up HTMX for dynamic content loading
- [ ] Add Alpine.js for interactive UI state
- [ ] Implement form submission and validation
- [ ] Add progress saving

### 6.6 Step 2: Origin (Background & Species)
- [ ] Create origin page with tabs
- [ ] Create background selection interface
- [ ] Create background details panel with synergy indicators
- [ ] Create species selection interface
- [ ] Create species details panel with trait displays
- [ ] Create language selection dropdown
- [ ] Implement Origin feat choice interface (if needed)
- [ ] Wire up tab switching with Alpine.js
- [ ] Implement form submission
- [ ] Show combined origin summary after both selected

### 6.7 Step 3: Ability Scores
- [ ] Create ability scores page
- [ ] Create method selection cards (Standard Array, Point Buy, Roll)
- [ ] Implement Standard Array interface:
  - Draggable score assignment or click-to-assign
  - Real-time impact display
  - Smart suggestions
- [ ] Implement Point Buy interface:
  - Point pool counter
  - +/- controls for each ability
  - Cost table reference
  - Presets
- [ ] Implement Roll Dice interface:
  - Dice rolling animation
  - Results display
  - Score assignment
  - Optional reroll
- [ ] Create real-time stat impact panel:
  - HP calculation
  - AC preview
  - Attack bonus
  - Skill modifiers
  - Saving throws
- [ ] Wire up calculations with Alpine.js
- [ ] Implement form submission

### 6.8 Step 4: Alignment
- [ ] Create alignment page
- [ ] Create 3x3 alignment grid
- [ ] Create alignment detail panels
- [ ] Add skip option
- [ ] Implement selection and submission
- [ ] Add optional alignment nuance sliders

### 6.9 Step 5: Equipment & Spells
- [ ] Create equipment page with tabs
- [ ] Create equipment slot visualization (paper doll)
- [ ] Create equipment inventory list
- [ ] Create equipment details modal
- [ ] Create armor comparison table
- [ ] Create weapon comparison table
- [ ] Create AC calculator widget
- [ ] Implement equip/unequip interactions
- [ ] Create shopping interface (if gold option)
- [ ] Create encumbrance tracker
- [ ] Create spell selection interface (for spellcasters):
  - Cantrip grid
  - 1st-level spell grid
  - Spell filters and search
  - Spell details modal
- [ ] Wire up all interactions with Alpine.js and HTMX
- [ ] Implement form submission

### 6.10 Step 6: Character Details
- [ ] Create character details page
- [ ] Create name input with generator button
- [ ] Create physical characteristics inputs
- [ ] Create pronouns dropdown
- [ ] Create character portrait upload:
  - Drag-drop interface
  - Preview
  - Upload to S3
- [ ] Create personality fields with prompts
- [ ] Create backstory rich text editor
- [ ] Create additional detail fields
- [ ] Implement character summary preview
- [ ] Implement form submission

### 6.11 Character Review & Completion
- [ ] Create character review page
- [ ] Create celebration header with animation
- [ ] Create complete character sheet preview
- [ ] Implement section expansion/collapse
- [ ] Create export options:
  - Download PDF button
  - Export JSON button
  - Share link button
- [ ] Create edit options (jump to step)
- [ ] Create "Create Another" button
- [ ] Wire up all actions

### 6.12 Character Sheet View
- [ ] Create full character sheet display page
- [ ] Format all character data attractively
- [ ] Make sections collapsible
- [ ] Add print styles (CSS @media print)
- [ ] Add ability to track resource usage (HP, spell slots, feature uses)
- [ ] Create "Level Up" button (grayed out initially)

### 6.13 Interactive Features
- [ ] Implement auto-save every 30 seconds
- [ ] Add "changes saved" indicator
- [ ] Add loading states for all async operations
- [ ] Add error handling and user-friendly error messages
- [ ] Implement tooltips on hover for all game terms
- [ ] Add keyboard navigation support
- [ ] Implement responsive design breakpoints
- [ ] Test on mobile devices

### 6.14 Help & Onboarding
- [ ] Create help sidebar/modal system
- [ ] Add contextual help content for each step
- [ ] Create glossary page with searchable terms
- [ ] Add first-time user tutorial (optional)
- [ ] Create "How to Play Your Class" guides (optional)

---

## Phase 7: AWS & Zappa Deployment

### 7.1 Prepare for Deployment
- [ ] Update `requirements.txt` with all dependencies
- [ ] Freeze exact versions: `pip freeze > requirements.txt`
- [ ] Create `requirements-dev.txt` for dev-only dependencies
- [ ] Set all secrets as environment variables (never commit!)
- [ ] Create comprehensive `.env.example`
- [ ] Update `.gitignore` to exclude sensitive files
- [ ] Test that `DEBUG=False` works locally

### 7.2 Configure Production Settings
- [ ] Update `settings/production.py`:
  - Set `DEBUG=False`
  - Configure `ALLOWED_HOSTS` with domain/API Gateway URL
  - Set up S3 for static files (django-storages)
  - Set up S3 for media files
  - Configure RDS database URL
  - Set secure cookie settings
  - Configure CORS for frontend domain
  - Set up logging to CloudWatch
- [ ] Configure static file collection for S3:
  - `AWS_STORAGE_BUCKET_NAME`
  - `AWS_S3_CUSTOM_DOMAIN`
  - `STATIC_URL` and `MEDIA_URL`

### 7.3 Zappa Configuration
- [ ] Update `zappa_settings.json` with production values:
  - Correct S3 bucket
  - VPC configuration for RDS access
  - Environment variables for secrets
  - Memory and timeout settings (adjust based on testing)
  - CloudWatch log retention
  - Lambda runtime (Python 3.11)
  - Exclude unnecessary files: `exclude: ["*.pyc", "tests/*"]`
- [ ] Add custom domain configuration (if using):
  ```json
  "domain": "api.yourdomain.com",
  "certificate_arn": "arn:aws:acm:..."
  ```

### 7.4 Database Migration Strategy
- [ ] Plan migration strategy for RDS:
  - Option A: Import fixtures after deploy
  - Option B: Export local DB and import to RDS
- [ ] Create database backup before any production changes
- [ ] Test migrations locally against PostgreSQL (not SQLite)
- [ ] Create management command to verify data integrity

### 7.5 Initial Deployment
- [ ] Deploy to dev environment:
  ```bash
  zappa deploy dev
  ```
- [ ] Verify deployment successful
- [ ] Check CloudWatch logs for errors
- [ ] Test API Gateway endpoint is accessible
- [ ] Run database migrations on RDS:
  ```bash
  zappa manage dev migrate
  ```
- [ ] Create superuser on production:
  ```bash
  zappa manage dev createsuperuser
  ```
- [ ] Import game content data:
  ```bash
  zappa manage dev import_dnd_data
  ```
- [ ] Test that admin panel is accessible
- [ ] Verify static files are serving from S3
- [ ] Test media upload (character portraits) to S3

### 7.6 Update Deployment
- [ ] For subsequent updates, use:
  ```bash
  zappa update dev
  ```
- [ ] Monitor CloudWatch during updates
- [ ] Test critical paths after each deployment
- [ ] Rollback if issues: `zappa rollback dev -n 1`

### 7.7 Environment Management
- [ ] Deploy production environment:
  ```bash
  zappa deploy production
  ```
- [ ] Set up separate RDS instance for production
- [ ] Configure production domain with Route 53
- [ ] Set up SSL certificate with ACM
- [ ] Configure production environment variables
- [ ] Run production migrations and data import
- [ ] Test production environment thoroughly

### 7.8 Monitoring & Logging
- [ ] Set up CloudWatch alarms for:
  - Lambda errors
  - Lambda timeouts
  - High latency (> 3 seconds)
  - API Gateway 5xx errors
  - RDS connection issues
- [ ] Configure CloudWatch log groups retention (7-30 days)
- [ ] Set up CloudWatch dashboard with key metrics:
  - Request count
  - Error rate
  - Average response time
  - Lambda concurrent executions
  - RDS connections
- [ ] Configure SNS alerts for critical errors
- [ ] Set up email notifications for alarms

### 7.9 Performance Optimization
- [ ] Enable Lambda function caching (if applicable)
- [ ] Configure API Gateway caching for read-heavy endpoints:
  - GET /api/classes
  - GET /api/spells
  - GET /api/equipment
- [ ] Optimize database queries:
  - Add `select_related()` for foreign keys
  - Add `prefetch_related()` for many-to-many
  - Review Django Debug Toolbar query analysis
- [ ] Set up CloudFront CDN for static/media files
- [ ] Configure GZIP compression
- [ ] Minimize Lambda cold starts:
  - Keep functions warm with CloudWatch Events (optional)
  - Optimize package size
  - Reduce dependencies where possible

### 7.10 Security Hardening
- [ ] Enable AWS WAF on API Gateway (optional, costs extra)
- [ ] Configure rate limiting on API Gateway
- [ ] Set up CORS properly for frontend domain only
- [ ] Enable HTTPS only (redirect HTTP to HTTPS)
- [ ] Use AWS Secrets Manager for sensitive config
- [ ] Enable RDS encryption at rest
- [ ] Enable S3 bucket encryption
- [ ] Set up S3 bucket policies (restrict public access except static files)
- [ ] Configure security groups restrictively
- [ ] Review IAM roles and permissions (principle of least privilege)
- [ ] Enable CloudTrail for audit logging
- [ ] Set up AWS GuardDuty for threat detection (optional)

### 7.11 Backup & Disaster Recovery
- [ ] Enable automated RDS backups:
  - Set retention period (7-30 days)
  - Configure backup window
- [ ] Enable RDS Multi-AZ for production (high availability)
- [ ] Set up S3 versioning for media bucket
- [ ] Create disaster recovery plan documentation
- [ ] Test database restore procedure
- [ ] Set up cross-region replication for S3 (optional)

### 7.12 Cost Optimization
- [ ] Review AWS cost allocation tags
- [ ] Set up billing alerts:
  - Alert at $50, $100, $200 thresholds
- [ ] Monitor Lambda execution time (optimize to reduce costs)
- [ ] Review RDS instance sizing (start small, scale as needed)
- [ ] Consider Reserved Instances for production (if consistent usage)
- [ ] Clean up old Lambda versions (Zappa can accumulate these)
- [ ] Set S3 lifecycle policies for old objects
- [ ] Review CloudWatch log retention (logs cost money)

---

## Phase 8: Testing

### 8.1 Unit Tests
- [ ] Set up pytest and pytest-django
- [ ] Configure test database settings
- [ ] Create `conftest.py` with common fixtures
- [ ] Write model tests:
  - Test all model creation
  - Test model methods and properties
  - Test model relationships
  - Test custom managers/querysets
- [ ] Write serializer tests:
  - Test serialization
  - Test deserialization
  - Test validation errors
- [ ] Write service layer tests:
  - Test CharacterCalculationService
  - Test CharacterValidationService
  - Test DiceRollerService
  - Test RecommendationService
- [ ] Write utility function tests
- [ ] Aim for 70%+ code coverage on business logic

### 8.2 API Integration Tests
- [ ] Install pytest-django and DRF test tools
- [ ] Write API endpoint tests for:
  - Authentication (register, login, logout)
  - User profile CRUD
  - Character CRUD operations
  - Character step-by-step creation flow
  - All game content endpoints
  - Spell filtering and search
  - Equipment filtering
  - Export functionality
- [ ] Test permissions:
  - Unauthenticated access
  - Unauthorized access (other user's characters)
  - Proper authenticated access
- [ ] Test edge cases and error handling
- [ ] Test rate limiting
- [ ] Test pagination

### 8.3 End-to-End Tests
- [ ] Set up Playwright or Selenium for E2E tests
- [ ] Write critical path tests:
  - Complete character creation flow (all 6 steps)
  - Edit existing character
  - Delete character
  - Export character
  - Share character
- [ ] Test on multiple browsers:
  - Chrome
  - Firefox
  - Safari
  - Edge
- [ ] Test responsive design (mobile, tablet, desktop)
- [ ] Test with screen reader (accessibility)

### 8.4 Performance Testing
- [ ] Use locust.io or Apache JMeter for load testing
- [ ] Test API endpoints under load:
  - 100 concurrent users
  - 1000 requests per minute
- [ ] Identify bottlenecks
- [ ] Test database query performance with large datasets
- [ ] Profile slow endpoints with Django Debug Toolbar
- [ ] Optimize N+1 query problems

### 8.5 Security Testing
- [ ] Test authentication and authorization thoroughly
- [ ] Test SQL injection prevention (Django ORM should handle this)
- [ ] Test XSS prevention
- [ ] Test CSRF protection
- [ ] Test file upload security (character portraits)
- [ ] Test rate limiting effectiveness
- [ ] Review OWASP Top 10 vulnerabilities
- [ ] Run security scan with tools like:
  - Bandit (for Python code)
  - Safety (for dependency vulnerabilities)
  - npm audit (if using npm packages)

### 8.6 User Acceptance Testing
- [ ] Recruit beta testers (D&D players)
- [ ] Create test scenarios for each user journey
- [ ] Collect feedback on:
  - Ease of use
  - Clarity of instructions
  - UI/UX issues
  - Bugs and errors
  - Feature requests
- [ ] Prioritize and address feedback
- [ ] Iterate based on user testing

---

## Phase 9: Documentation

### 9.1 Code Documentation
- [ ] Add docstrings to all models, views, serializers, services
- [ ] Follow PEP 257 docstring conventions
- [ ] Document complex algorithms and business logic
- [ ] Add inline comments for non-obvious code
- [ ] Document all environment variables in `.env.example`

### 9.2 API Documentation
- [ ] Ensure all API endpoints have OpenAPI documentation
- [ ] Add example requests and responses
- [ ] Document authentication requirements
- [ ] Document rate limiting
- [ ] Document error codes and messages
- [ ] Create API usage guide

### 9.3 Developer Documentation
- [ ] Create `README.md` with:
  - Project description
  - Tech stack
  - Prerequisites
  - Local setup instructions
  - How to run tests
  - How to deploy
  - Contributing guidelines
- [ ] Create `CONTRIBUTING.md` with:
  - Code style guide
  - Git workflow
  - PR process
  - Testing requirements
- [ ] Create `DEPLOYMENT.md` with:
  - Deployment checklist
  - Environment setup
  - Rollback procedures
  - Troubleshooting guide
- [ ] Create architecture diagrams:
  - System architecture
  - Database schema (ER diagram)
  - API flow diagrams
- [ ] Document AWS infrastructure setup

### 9.4 User Documentation
- [ ] Create user guide:
  - How to create a character (step-by-step)
  - How to edit a character
  - How to export/share characters
  - FAQ section
- [ ] Create video tutorials (optional):
  - Getting started
  - Creating your first character
  - Advanced features
- [ ] Create D&D rules primer for newcomers:
  - What is D&D?
  - Basic concepts (classes, races, abilities, etc.)
  - Glossary of terms
- [ ] Create troubleshooting guide for users

### 9.5 Admin Documentation
- [ ] Create admin guide:
  - How to manage users
  - How to update game content
  - How to moderate shared characters
  - How to handle reports/issues
- [ ] Document admin panel features
- [ ] Create content moderation guidelines

---

## Phase 10: CI/CD & DevOps

### 10.1 Version Control Best Practices
- [ ] Set up GitHub repository (or GitLab/Bitbucket)
- [ ] Configure branch protection rules:
  - Require PR reviews
  - Require CI checks to pass
  - No direct commits to main/production
- [ ] Define branching strategy:
  - `main` - production
  - `develop` - staging/development
  - `feature/*` - feature branches
  - `hotfix/*` - emergency fixes
- [ ] Write good commit messages (conventional commits)
- [ ] Use semantic versioning for releases

### 10.2 Continuous Integration
- [ ] Set up GitHub Actions (or alternative CI):
  - `.github/workflows/test.yml`
- [ ] Configure CI pipeline:
  - Checkout code
  - Set up Python environment
  - Install dependencies
  - Run linting (flake8, black, isort)
  - Run security checks (bandit, safety)
  - Run unit tests
  - Run integration tests
  - Generate coverage report
  - Upload coverage to Codecov (optional)
- [ ] Set up CI for pull requests
- [ ] Require CI to pass before merge
- [ ] Configure status checks in GitHub

### 10.3 Continuous Deployment
- [ ] Set up GitHub Actions for deployment:
  - `.github/workflows/deploy.yml`
- [ ] Configure CD pipeline:
  - Trigger on push to `develop` → deploy to dev
  - Trigger on push to `main` → deploy to production (with approval)
- [ ] Add deployment steps:
  - Run tests first
  - Deploy with Zappa
  - Run migrations
  - Verify deployment health
  - Send notification (Slack, email)
- [ ] Set up rollback automation on failure
- [ ] Configure deployment notifications

### 10.4 Code Quality Tools
- [ ] Set up pre-commit hooks:
  - Install pre-commit: `pip install pre-commit`
  - Create `.pre-commit-config.yaml`
  - Run black (code formatting)
  - Run isort (import sorting)
  - Run flake8 (linting)
  - Run mypy (type checking) - optional
- [ ] Configure black for consistent formatting
- [ ] Configure isort for import organization
- [ ] Configure flake8 rules
- [ ] Set up SonarQube or CodeClimate (optional)

### 10.5 Monitoring & Alerting
- [ ] Set up error tracking with Sentry:
  - Install sentry-sdk
  - Configure in Django settings
  - Test error reporting
- [ ] Configure Sentry alerts for:
  - New errors
  - Error frequency spikes
  - Performance degradation
- [ ] Set up application performance monitoring (APM):
  - Use Sentry Performance or New Relic
  - Monitor slow endpoints
  - Track database query performance
- [ ] Create on-call rotation (if team)
- [ ] Create incident response runbook

### 10.6 Database Management
- [ ] Create database migration checklist
- [ ] Set up automated backup verification
- [ ] Create data seeding scripts for environments
- [ ] Document data migration procedures
- [ ] Set up database monitoring:
  - Connection count
  - Query performance
  - Disk usage
  - CPU utilization

---

## Phase 11: Polish & Launch Preparation

### 11.1 UX/UI Polish
- [ ] Conduct usability testing with target users
- [ ] Fix all critical UX issues
- [ ] Ensure consistent styling across all pages
- [ ] Add micro-interactions and animations (subtle)
- [ ] Optimize page load times (< 3 seconds)
- [ ] Test all error messages are user-friendly
- [ ] Add empty states with helpful guidance
- [ ] Ensure all interactive elements have hover/focus states
- [ ] Test keyboard navigation thoroughly
- [ ] Test with screen readers

### 11.2 Accessibility (WCAG 2.1 AA Compliance)
- [ ] Run automated accessibility tests (aXe, WAVE)
- [ ] Ensure proper heading hierarchy
- [ ] Add ARIA labels where needed
- [ ] Ensure sufficient color contrast (4.5:1 for text)
- [ ] Make all functionality keyboard accessible
- [ ] Add skip navigation links
- [ ] Test with screen reader (NVDA, JAWS, VoiceOver)
- [ ] Ensure forms have proper labels and error messages
- [ ] Add focus indicators
- [ ] Test with high contrast mode

### 11.3 Performance Optimization
- [ ] Optimize images (compress, use WebP)
- [ ] Implement lazy loading for images
- [ ] Minify CSS and JavaScript
- [ ] Enable browser caching
- [ ] Optimize database indexes
- [ ] Review and optimize slow API endpoints
- [ ] Implement pagination for large lists
- [ ] Add loading skeletons for better perceived performance
- [ ] Test on slow network connections (3G)
- [ ] Achieve Lighthouse score > 90 in all categories

### 11.4 SEO Optimization
- [ ] Add proper meta tags (title, description)
- [ ] Create `sitemap.xml`
- [ ] Create `robots.txt`
- [ ] Add Open Graph tags for social sharing
- [ ] Add Twitter Card tags
- [ ] Implement structured data (Schema.org)
- [ ] Ensure proper heading hierarchy (H1, H2, etc.)
- [ ] Add alt text to all images
- [ ] Create canonical URLs
- [ ] Optimize page titles and descriptions

### 11.5 Legal & Compliance
- [ ] Create Terms of Service
- [ ] Create Privacy Policy (GDPR compliant if EU users)
- [ ] Add cookie consent banner (if using cookies)
- [ ] Create Disclaimer (D&D is Wizards of the Coast IP)
- [ ] Add copyright notices
- [ ] Ensure compliance with COPPA (if allowing users under 13)
- [ ] Create DMCA policy (if allowing user content)
- [ ] Add contact information
- [ ] Create acceptable use policy

### 11.6 Content Creation
- [ ] Write homepage copy
- [ ] Create "About" page
- [ ] Write feature descriptions
- [ ] Create tutorial content
- [ ] Write blog posts about features (optional)
- [ ] Create social media content
- [ ] Record demo videos
- [ ] Create marketing materials

### 11.7 Launch Checklist
- [ ] Final security review
- [ ] Final performance review
- [ ] Test all critical user flows
- [ ] Verify all integrations working
- [ ] Check all third-party services are configured
- [ ] Verify monitoring and alerting is working
- [ ] Confirm backup strategy is in place
- [ ] Test disaster recovery plan
- [ ] Review and test rollback procedures
- [ ] Prepare launch announcement
- [ ] Set up customer support channels
- [ ] Create bug report template
- [ ] Brief team on launch procedures

### 11.8 Soft Launch (Beta)
- [ ] Launch to limited audience (beta testers)
- [ ] Monitor closely for issues
- [ ] Collect feedback actively
- [ ] Fix critical bugs quickly
- [ ] Iterate based on feedback
- [ ] Gradually increase user base
- [ ] Monitor server load and scale as needed

### 11.9 Public Launch
- [ ] Announce on social media
- [ ] Post on Reddit (r/DnD, r/dndnext, etc.)
- [ ] Share on D&D Discord servers
- [ ] Submit to product directories (Product Hunt, etc.)
- [ ] Email existing beta users
- [ ] Post on personal/company blog
- [ ] Monitor for increased traffic/load
- [ ] Be ready to respond to support requests
- [ ] Monitor error rates and performance
- [ ] Celebrate! 🎉

---

## Phase 12: Post-Launch & Maintenance

### 12.1 User Feedback Collection
- [ ] Set up feedback mechanism (in-app widget, email, form)
- [ ] Monitor social media mentions
- [ ] Track feature requests
- [ ] Monitor bug reports
- [ ] Conduct user surveys
- [ ] Set up analytics (Google Analytics, Mixpanel, etc.)
- [ ] Track key metrics:
  - New user signups
  - Character creation completion rate
  - Daily/Monthly active users
  - Session duration
  - Most popular classes/species
  - Drop-off points in creation flow

### 12.2 Bug Fixing & Maintenance
- [ ] Prioritize bugs (critical, high, medium, low)
- [ ] Fix critical bugs immediately
- [ ] Create regular maintenance schedule
- [ ] Keep dependencies updated (security patches)
- [ ] Monitor for security vulnerabilities
- [ ] Review and respond to error reports in Sentry
- [ ] Clean up old data (archived characters, expired sessions)
- [ ] Optimize database as data grows

### 12.3 Feature Development Roadmap
**Phase 1 Enhancements:**
- [ ] Character leveling up feature
- [ ] Multiclassing support
- [ ] Character comparison tool
- [ ] Party builder (link characters in same campaign)
- [ ] Character templates (quick start builds)

**Phase 2 Enhancements:**
- [ ] Magic items database and assignment
- [ ] Homebrew content creator
- [ ] Character journal/notes
- [ ] Session tracker
- [ ] Dice roller with history
- [ ] Initiative tracker

**Phase 3 Enhancements:**
- [ ] Mobile app (React Native)
- [ ] VTT integrations (deeper integration)
- [ ] DM tools (campaign management)
- [ ] Character marketplace (share builds)
- [ ] Community features (forums, guides)

### 12.4 Marketing & Growth
- [ ] Create content marketing strategy
- [ ] Write SEO-optimized blog posts
- [ ] Create video content (YouTube)
- [ ] Engage with D&D community
- [ ] Partner with D&D content creators
- [ ] Run social media campaigns
- [ ] Consider paid advertising (Google Ads, Facebook Ads)
- [ ] Track conversion funnels
- [ ] Optimize for user acquisition and retention

### 12.5 Monetization (Optional)
If planning to monetize:
- [ ] Premium features planning:
  - Unlimited characters
  - Custom homebrew content
  - Advanced character templates
  - Priority support
  - Ad-free experience
- [ ] Implement payment processing (Stripe)
- [ ] Create subscription tiers
- [ ] Implement paywall logic
- [ ] Ensure free tier is valuable
- [ ] Be transparent about pricing

### 12.6 Scaling Considerations
- [ ] Monitor costs as usage grows
- [ ] Optimize for scale:
  - Database query optimization
  - Implement caching (Redis)
  - Consider CDN for all static assets
  - Evaluate Lambda alternatives if needed (ECS, EKS)
- [ ] Plan for traffic spikes
- [ ] Consider read replicas for database
- [ ] Implement background job processing (Celery) if needed
- [ ] Monitor and optimize costs continuously

---

## Appendix: Useful Commands & References

### Django Management Commands
```bash
# Local development
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py shell
python manage.py test
python manage.py collectstatic

# Custom commands
python manage.py import_dnd_data
python manage.py validate_data
```

### Zappa Commands
```bash
# Initial deployment
zappa deploy dev
zappa deploy production

# Updates
zappa update dev
zappa update production

# Management commands via Zappa
zappa manage dev migrate
zappa manage dev createsuperuser
zappa manage dev "import_dnd_data"

# Logs
zappa tail dev
zappa tail production --since 1h

# Status
zappa status dev

# Rollback
zappa rollback dev -n 1

# Undeploy
zappa undeploy dev
```

### AWS CLI Commands
```bash
# S3
aws s3 ls s3://dnd-creator-media/
aws s3 cp character.jpg s3://dnd-creator-media/portraits/

# RDS
aws rds describe-db-instances
aws rds create-db-snapshot

# Lambda
aws lambda list-functions
aws lambda get-function --function-name dnd-creator-dev

# CloudWatch
aws logs tail /aws/lambda/dnd-creator-dev --follow
```

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/character-leveling

# Make changes, commit
git add .
git commit -m "feat: add character leveling system"

# Push and create PR
git push origin feature/character-leveling

# After PR merged, clean up
git checkout main
git pull
git branch -d feature/character-leveling
```

### Testing Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest characters/tests/test_models.py

# Run specific test
pytest characters/tests/test_models.py::TestCharacterModel::test_hp_calculation

# Run with verbose output
pytest -v

# Run and stop at first failure
pytest -x
```

---

## Important Notes & Best Practices

### Django Best Practices
- Always use environment variables for secrets
- Never commit `.env` file
- Use Django's built-in security features (CSRF, XSS protection)
- Follow Django coding style guide
- Keep views thin, put business logic in services
- Use Django ORM efficiently (avoid N+1 queries)
- Use transactions for data integrity
- Write migrations carefully (test rollback)

### Zappa Best Practices
- Keep Lambda functions small (< 50MB compressed)
- Use VPC only when necessary (adds cold start time)
- Set appropriate timeout values (default 30s)
- Use environment variables for configuration
- Monitor cold starts and optimize
- Clean up old Lambda versions periodically
- Use separate S3 buckets for Zappa and media
- Test deployments in dev before production

### AWS Best Practices
- Follow principle of least privilege for IAM
- Enable CloudTrail for audit logging
- Use security groups restrictively
- Enable encryption at rest for all data
- Regular security audits
- Monitor costs continuously
- Set up billing alerts
- Use tags for resource organization
- Regular backups and test restore procedures

### Security Best Practices
- Keep all dependencies updated
- Regular security scans
- Use HTTPS everywhere
- Implement proper authentication and authorization
- Validate all user input
- Sanitize all output
- Use parameterized queries (Django ORM does this)
- Implement rate limiting
- Log security events
- Regular penetration testing

---

## Success Criteria

**MVP Launch Success Criteria:**
- [ ] Users can create complete characters (all 6 steps)
- [ ] All 13 classes available with features
- [ ] All backgrounds and species available
- [ ] Spell selection working for all casters
- [ ] Character sheet export (PDF and JSON)
- [ ] Mobile responsive design
- [ ] Page load time < 3 seconds
- [ ] API response time < 500ms (p95)
- [ ] Zero critical bugs
- [ ] 95%+ uptime
- [ ] Positive user feedback

**6 Month Success Metrics:**
- 1,000+ registered users
- 5,000+ characters created
- 70%+ character creation completion rate
- 30%+ user retention (30 days)
- 4.0+ star rating (if applicable)
- Community engagement (social media, forums)

---

## Timeline Estimate

**Phase 1-2 (Setup & Models): 2-3 weeks**
**Phase 3 (Admin & Data): 1-2 weeks**
**Phase 4 (API): 2-3 weeks**
**Phase 5 (Business Logic): 1-2 weeks**
**Phase 6 (Frontend): 4-6 weeks**
**Phase 7 (Deployment): 1 week**
**Phase 8 (Testing): 2 weeks**
**Phase 9-10 (Docs & CI/CD): 1 week**
**Phase 11 (Polish & Launch): 2 weeks**

**Total: 16-22 weeks (4-5.5 months) for MVP**

---

## Resources & References

### Django Documentation
- https://docs.djangoproject.com/
- https://www.django-rest-framework.org/

### Zappa Documentation
- https://github.com/zappa/Zappa
- https://romandc.com/zappa-django-guide/

### AWS Documentation
- https://aws.amazon.com/lambda/
- https://aws.amazon.com/rds/
- https://aws.amazon.com/s3/

### D&D Rules
- D&D Beyond: https://www.dndbeyond.com/
- D&D 5e SRD: https://5e.tools/
- 2024 Player's Handbook

### Tools & Libraries
- HTMX: https://htmx.org/
- Alpine.js: https://alpinejs.dev/
- Tailwind CSS: https://tailwindcss.com/
- Django Storages: https://django-storages.readthedocs.io/

---

## Getting Help

- Django Discord: https://discord.gg/django
- AWS Support: Through AWS Console
- Stack Overflow: Tag questions with [django], [zappa], [aws-lambda]
- Reddit: r/django, r/aws
- GitHub Issues: For specific library issues

---

**Remember:** This is an ambitious project. Break it into smaller, manageable chunks. Focus on getting a basic character creator working first (classes, backgrounds, species, abilities), then iterate and add features. Ship early, get feedback, and improve continuously!

**Good luck! May your dice rolls always be natural 20s! 🎲**