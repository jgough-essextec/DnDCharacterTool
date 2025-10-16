"""
Main orchestrator command to import all D&D data in the correct order.

Usage:
    python manage.py import_dnd_data                # Import all data
    python manage.py import_dnd_data --phase 1     # Import only Phase 1 (core reference data)
    python manage.py import_dnd_data --clear       # Clear existing data before importing
    python manage.py import_dnd_data --dry-run     # Preview what would be imported
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Import all D&D 5e data from JSON files in the correct order'

    def add_arguments(self, parser):
        parser.add_argument(
            '--phase',
            type=int,
            choices=[1, 2, 3, 4, 5],
            help='Import only a specific phase (1-5)'
        )
        parser.add_argument(
            '--data-dir',
            type=str,
            default='data',
            help='Directory containing the JSON data files'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing data before importing'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode (no database changes)'
        )

    def handle(self, *args, **options):
        phase = options.get('phase')
        data_dir = options.get('data_dir', 'data')
        clear = options.get('clear', False)
        dry_run = options.get('dry_run', False)
        verbosity = options.get('verbosity', 1)

        # Common options for all commands
        common_options = {
            'data_dir': data_dir,
            'verbosity': verbosity,
        }

        if dry_run:
            common_options['dry_run'] = True

        # Phase definitions
        phases = {
            1: {
                'name': 'Core Reference Data',
                'commands': [
                    ('import_skills', 'Skills'),
                    ('import_languages', 'Languages'),
                ]
            },
            2: {
                'name': 'Character Options',
                'commands': [
                    ('import_species', 'Species/Races'),
                    ('import_classes', 'Classes'),
                    ('import_backgrounds', 'Backgrounds'),
                    ('import_feats', 'Feats'),
                ]
            },
            3: {
                'name': 'Equipment',
                'commands': [
                    ('import_equipment', 'Equipment'),
                ]
            },
            4: {
                'name': 'Spells',
                'commands': [
                    ('import_spells', 'Spells'),
                ]
            },
            5: {
                'name': 'Relationships',
                'commands': [
                    ('link_relationships', 'Entity Relationships'),
                ]
            }
        }

        # Header
        self.stdout.write("="*60)
        self.stdout.write(self.style.SUCCESS("D&D 5E DATA IMPORT"))
        self.stdout.write("="*60)

        if dry_run:
            self.stdout.write(self.style.WARNING("Running in DRY-RUN mode - no changes will be saved"))

        # Determine which phases to run
        if phase:
            phases_to_run = {phase: phases[phase]}
        else:
            phases_to_run = phases

        # Execute phases
        for phase_num, phase_info in phases_to_run.items():
            self.stdout.write(f"\n{'-'*60}")
            self.stdout.write(self.style.SUCCESS(f"PHASE {phase_num}: {phase_info['name']}"))
            self.stdout.write(f"{'-'*60}")

            if not phase_info['commands']:
                self.stdout.write(self.style.WARNING("No commands available for this phase yet"))
                continue

            for command_name, description in phase_info['commands']:
                self.stdout.write(f"\n>> Importing {description}...")

                try:
                    # Add clear option only for the first command of Phase 1
                    cmd_options = common_options.copy()
                    if clear and phase_num == 1 and command_name == phase_info['commands'][0][0]:
                        cmd_options['clear'] = True

                    call_command(command_name, **cmd_options)

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed to import {description}: {str(e)}")
                    )
                    if verbosity >= 2:
                        import traceback
                        traceback.print_exc()

                    # Ask whether to continue
                    if not dry_run:
                        response = input("\nContinue with remaining imports? (y/N): ")
                        if response.lower() != 'y':
                            self.stdout.write(self.style.ERROR("Import cancelled by user"))
                            return

        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("IMPORT COMPLETE"))
        self.stdout.write("="*60)

        # Show next steps
        if not phase or phase == 5:
            self.stdout.write("\nNext steps:")
            self.stdout.write("1. Verify data in Django admin: python manage.py runserver")
            self.stdout.write("2. Create sample characters to test relationships")
            self.stdout.write("3. Run tests: python manage.py test game_content")

    def _print_phase_summary(self, phase_num, phase_name):
        """Print a summary of what will be imported in a phase."""
        summaries = {
            1: [
                "- Skills: 18 core D&D skills (Acrobatics, Athletics, etc.)",
                "- Languages: Standard and exotic languages (Common, Elvish, Draconic, etc.)"
            ],
            2: [
                "- Species: Player character races and their traits",
                "- Classes: Character classes with features and subclasses",
                "- Backgrounds: Character backgrounds with proficiencies",
                "- Feats: Origin, general, and fighting style feats"
            ],
            3: [
                "- Weapons: Simple and martial weapons with properties",
                "- Armor: Light, medium, and heavy armor",
                "- Equipment: Adventuring gear, tools, and other items"
            ],
            4: [
                "- Spells: Cantrips through 9th level spells",
                "- Spell details: Components, duration, range, etc.",
                "- Class spell lists: Which classes can cast which spells"
            ],
            5: [
                "- Link spells to classes",
                "- Link features to subclasses",
                "- Link origin feats to backgrounds",
                "- Validate all relationships"
            ]
        }

        if phase_num in summaries:
            self.stdout.write(f"\nPhase {phase_num} - {phase_name} includes:")
            for item in summaries[phase_num]:
                self.stdout.write(item)