"""
Base importer class for D&D data ETL operations.
"""

import json
import re
from pathlib import Path
from django.db import transaction
from django.core.management.base import BaseCommand


class BaseImporter(BaseCommand):
    """Base class for all D&D data importers."""

    # Valid sources for 5e content (excluding 2024/5.5e)
    VALID_SOURCES = [
        'PHB', 'XGE', 'TCE', 'SCAG', 'MM', 'VGM', 'MTF', 'GGR', 'AI', 'EGW',
        'MOT', 'IDRotF', 'TCoE', 'FTD', 'SCC', 'DSotDQ', 'BMT', 'BPG', 'SAiS',
        'EGtW', 'OotA', 'PotA', 'SKT', 'TftYP', 'ToA', 'WDH', 'WDMM', 'GoS',
        'BGDiA', 'DC', 'DHM', 'IMR', 'SDW', 'SLW', 'AAG', 'PSA', 'PSI', 'PSK',
        'PSX', 'PSZ', 'HotDQ', 'RoT', 'LMoP', 'CoS', 'ALCoS', 'ALCurseOfStrahd',
        'DDAL', 'DDIA', 'DDEP', 'DDEX', 'VD', 'SCREEN', 'ScreenDungeonKit',
        'HEROES', 'RMR', 'RMBRE', 'AL', 'SatO', 'ToD', 'WDH', 'WDMM', 'GoS'
    ]

    EXCLUDED_SOURCES = ['XPHB', 'UA', 'UAClassFeatureVariants', 'homebrew']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verbosity = 1
        self.created_count = 0
        self.updated_count = 0
        self.skipped_count = 0
        self.errors = []
        self.data_path = Path('data')  # Default data directory

    def add_arguments(self, parser):
        """Add common command arguments."""
        parser.add_argument(
            '--data-dir',
            type=str,
            default='data',
            help='Directory containing the JSON data files (default: data)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode (no database changes)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before importing'
        )

    def handle(self, *args, **options):
        """Main entry point for the command."""
        self.verbosity = options.get('verbosity', 1)
        self.data_path = Path(options.get('data_dir', 'data'))

        if not self.data_path.exists():
            self.stdout.write(
                self.style.ERROR(f"Data directory {self.data_path} does not exist")
            )
            return

        if options.get('clear'):
            self.clear_existing_data()

        try:
            if options.get('dry_run'):
                self.stdout.write(self.style.WARNING("Running in DRY-RUN mode - no changes will be saved"))
                self.import_data()
            else:
                with transaction.atomic():
                    self.import_data()

            self.print_summary()

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Import failed: {str(e)}")
            )
            if self.verbosity >= 2:
                import traceback
                traceback.print_exc()

    def log(self, message, level=1, style=None):
        """Log a message based on verbosity level."""
        if self.verbosity >= level:
            if style:
                message = style(message)
            self.stdout.write(message)

    def is_valid_entry(self, entry):
        """Check if an entry should be imported based on source."""
        source = entry.get('source', '')

        # Skip if no source
        if not source:
            return False

        # Skip excluded sources (like XPHB - 2024 edition)
        if source in self.EXCLUDED_SOURCES:
            return False

        # Only include valid sources
        return source in self.VALID_SOURCES

    def clean_text(self, text):
        """Clean text by removing tags and formatting."""
        if not text:
            return ""

        # Remove common tags like {@creature ...}, {@spell ...}, etc.
        text = re.sub(r'\{@\w+\s+([^}|]+)(?:\|[^}]+)?\}', r'\1', text)

        # Remove dice notation tags
        text = re.sub(r'\{@dice\s+([^}]+)\}', r'\1', text)
        text = re.sub(r'\{@damage\s+([^}]+)\}', r'\1', text)

        # Clean up any remaining curly braces
        text = text.replace('{', '').replace('}', '')

        return text.strip()

    def parse_entries(self, entries):
        """Parse entries array into a single description string."""
        if not entries:
            return ""

        description_parts = []

        for entry in entries:
            if isinstance(entry, str):
                description_parts.append(self.clean_text(entry))
            elif isinstance(entry, dict):
                # Handle different entry types
                if entry.get('type') == 'list':
                    # Convert list items
                    items = entry.get('items', [])
                    for item in items:
                        if isinstance(item, str):
                            description_parts.append(f"• {self.clean_text(item)}")
                        elif isinstance(item, dict) and 'name' in item:
                            description_parts.append(f"• {item['name']}: {self.clean_text(item.get('entry', ''))}")
                elif 'entries' in entry:
                    # Recursive parsing
                    description_parts.append(self.parse_entries(entry['entries']))
                elif 'entry' in entry:
                    description_parts.append(self.clean_text(entry['entry']))

        return '\n\n'.join(filter(None, description_parts))

    def load_json_file(self, filename):
        """Load and return JSON data from a file."""
        file_path = self.data_path / filename

        if not file_path.exists():
            self.log(f"File {filename} not found", level=1, style=self.style.WARNING)
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.log(f"Loaded {filename}", level=2)
                return data
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON decode error in {filename}: {str(e)}")
            self.log(f"Failed to parse {filename}: {str(e)}", level=1, style=self.style.ERROR)
            return None
        except Exception as e:
            self.errors.append(f"Error loading {filename}: {str(e)}")
            self.log(f"Error loading {filename}: {str(e)}", level=1, style=self.style.ERROR)
            return None

    def import_data(self):
        """Main import method - must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement import_data()")

    def clear_existing_data(self):
        """Clear existing data - must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement clear_existing_data()")

    def validate_entry(self, entry):
        """Validate an entry - can be overridden by subclasses."""
        return True

    def transform_entry(self, entry):
        """Transform an entry - must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement transform_entry()")

    def save_entry(self, transformed_data):
        """Save an entry - must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement save_entry()")

    def print_summary(self):
        """Print import summary."""
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("IMPORT SUMMARY"))
        self.stdout.write("="*50)
        self.stdout.write(f"Created: {self.created_count}")
        self.stdout.write(f"Updated: {self.updated_count}")
        self.stdout.write(f"Skipped: {self.skipped_count}")

        if self.errors:
            self.stdout.write(f"\nErrors: {len(self.errors)}")
            if self.verbosity >= 2:
                for error in self.errors[:10]:  # Show first 10 errors
                    self.stdout.write(self.style.ERROR(f"  - {error}"))
                if len(self.errors) > 10:
                    self.stdout.write(f"  ... and {len(self.errors) - 10} more errors")
        else:
            self.stdout.write(self.style.SUCCESS("\nNo errors encountered!"))

        self.stdout.write("="*50 + "\n")