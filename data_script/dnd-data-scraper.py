"""
D&D 5e.tools Data Scraper
Crawls 5e.tools to gather all game content data for database population.

Requirements:
    pip install requests beautifulsoup4 lxml tqdm
"""

import json
import os
import time
import requests
import urllib3
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FiveEToolsScraper:
    """
    Scraper for 5e.tools data.
    
    Note: 5e.tools provides JSON data files directly which is more reliable
    than scraping HTML. This scraper uses their data repository.
    """
    
    # 5e.tools data repository (they host JSON files)
    BASE_URL = "https://5e.tools/data"
    GITHUB_RAW_URL = "https://raw.githubusercontent.com/TheGiddyLimit/TheGiddyLimit.github.io/master/data"
    
    def __init__(self, output_dir: str = "dnd_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DnD-Character-Creator-DataScraper/1.0'
        })
        
    def log(self, message: str):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def fetch_json(self, url: str, retries: int = 3) -> Optional[Dict]:
        """Fetch JSON data from URL with retry logic."""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30, verify=False)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                self.log(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.log(f"Failed to fetch {url} after {retries} attempts")
                    return None
                    
    def save_json(self, data: Any, filename: str):
        """Save data as JSON file."""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.log(f"Saved {filename}")
        
    def scrape_classes(self) -> List[Dict]:
        """Scrape all class data."""
        self.log("Scraping classes...")
        
        # 5e.tools stores class data in classes.json
        url = f"{self.GITHUB_RAW_URL}/class/class-artificer.json"
        
        classes_data = []
        class_files = [
            "class-artificer.json",
            "class-barbarian.json",
            "class-bard.json",
            "class-cleric.json",
            "class-druid.json",
            "class-fighter.json",
            "class-monk.json",
            "class-paladin.json",
            "class-ranger.json",
            "class-rogue.json",
            "class-sorcerer.json",
            "class-warlock.json",
            "class-wizard.json"
        ]
        
        for class_file in tqdm(class_files, desc="Fetching classes"):
            url = f"{self.GITHUB_RAW_URL}/class/{class_file}"
            data = self.fetch_json(url)
            if data and 'class' in data:
                for cls in data['class']:
                    # Extract relevant class information
                    class_info = {
                        'name': cls.get('name'),
                        'source': cls.get('source'),
                        'description': cls.get('fluff', {}).get('entries', []),
                        'hit_die': cls.get('hd', {}).get('faces', 8),
                        'primary_ability': self._extract_primary_ability(cls),
                        'saving_throws': cls.get('proficiency', []),
                        'armor_proficiencies': self._extract_proficiencies(cls, 'armor'),
                        'weapon_proficiencies': self._extract_proficiencies(cls, 'weapons'),
                        'tool_proficiencies': self._extract_proficiencies(cls, 'tools'),
                        'skill_proficiencies': self._extract_skill_proficiencies(cls),
                        'starting_equipment': cls.get('startingEquipment', {}),
                        'class_features': self._extract_class_features(cls),
                        'subclasses': cls.get('subclasses', []),
                        'spellcasting_ability': cls.get('spellcastingAbility'),
                        'caster_progression': cls.get('casterProgression')
                    }
                    classes_data.append(class_info)
                    
        self.save_json(classes_data, "classes.json")
        return classes_data
        
    def _extract_primary_ability(self, cls: Dict) -> Optional[str]:
        """Extract primary ability from class data."""
        if 'spellcastingAbility' in cls:
            return cls['spellcastingAbility']
        
        # For non-casters, infer from class name/type
        class_name = cls.get('name', '').lower()
        if class_name in ['barbarian', 'fighter', 'paladin']:
            return 'str'
        elif class_name in ['monk', 'ranger', 'rogue']:
            return 'dex'
        return None
        
    def _extract_proficiencies(self, cls: Dict, prof_type: str) -> List[str]:
        """Extract proficiencies of specific type."""
        proficiencies = []
        starting_prof = cls.get('startingProficiencies', {})
        
        if prof_type in starting_prof:
            prof_data = starting_prof[prof_type]
            if isinstance(prof_data, list):
                for item in prof_data:
                    if isinstance(item, str):
                        proficiencies.append(item)
                    elif isinstance(item, dict):
                        proficiencies.append(item.get('name', ''))
                        
        return proficiencies
        
    def _extract_skill_proficiencies(self, cls: Dict) -> Dict:
        """Extract skill proficiency information."""
        starting_prof = cls.get('startingProficiencies', {})
        skills = starting_prof.get('skills', [])
        
        skill_info = {
            'choose_count': 0,
            'available_skills': []
        }
        
        if isinstance(skills, list):
            for skill in skills:
                if isinstance(skill, dict):
                    if 'choose' in skill:
                        skill_info['choose_count'] = skill['choose'].get('count', 0)
                        skill_info['available_skills'] = skill['choose'].get('from', [])
                        
        return skill_info
        
    def _extract_class_features(self, cls: Dict) -> List[Dict]:
        """Extract class features by level."""
        features = []
        class_features_data = cls.get('classFeatures', [])
        
        for feature_ref in class_features_data:
            if isinstance(feature_ref, str):
                # Feature reference format: "Feature Name|ClassName|Source|Level"
                parts = feature_ref.split('|')
                if len(parts) >= 4:
                    features.append({
                        'name': parts[0],
                        'class_name': parts[1],
                        'source': parts[2],
                        'level': int(parts[3]) if parts[3].isdigit() else 1
                    })
            elif isinstance(feature_ref, dict):
                features.append(feature_ref)
                
        return features
        
    def scrape_backgrounds(self) -> List[Dict]:
        """Scrape all background data."""
        self.log("Scraping backgrounds...")
        
        url = f"{self.GITHUB_RAW_URL}/backgrounds.json"
        data = self.fetch_json(url)
        
        backgrounds_data = []
        if data and 'background' in data:
            for bg in tqdm(data['background'], desc="Processing backgrounds"):
                background_info = {
                    'name': bg.get('name'),
                    'source': bg.get('source'),
                    'description': bg.get('entries', []),
                    'skill_proficiencies': bg.get('skillProficiencies', []),
                    'tool_proficiencies': bg.get('toolProficiencies', []),
                    'language_proficiencies': bg.get('languageProficiencies', []),
                    'starting_equipment': bg.get('startingEquipment', []),
                    'feature_name': bg.get('featureName', ''),
                    'feature_entries': bg.get('featureEntries', []),
                    # Note: 2024 PHB backgrounds have ability score increases and origin feats
                    # These would need to be manually mapped or sourced differently
                }
                backgrounds_data.append(background_info)
                
        self.save_json(backgrounds_data, "backgrounds.json")
        return backgrounds_data
        
    def scrape_races(self) -> List[Dict]:
        """Scrape all race/species data."""
        self.log("Scraping races/species...")
        
        url = f"{self.GITHUB_RAW_URL}/races.json"
        data = self.fetch_json(url)
        
        races_data = []
        if data and 'race' in data:
            for race in tqdm(data['race'], desc="Processing races"):
                race_info = {
                    'name': race.get('name'),
                    'source': race.get('source'),
                    'description': race.get('entries', []),
                    'size': race.get('size', []),
                    'speed': race.get('speed', {}),
                    'darkvision': race.get('darkvision', 0),
                    'ability_scores': race.get('ability', []),  # Note: 2024 removes this
                    'traits': self._extract_race_traits(race),
                    'languages': race.get('languageProficiencies', []),
                    'subraces': race.get('_versions', [])
                }
                races_data.append(race_info)
                
        self.save_json(races_data, "races.json")
        return races_data
        
    def _extract_race_traits(self, race: Dict) -> List[Dict]:
        """Extract racial traits."""
        traits = []
        entries = race.get('entries', [])
        
        for entry in entries:
            if isinstance(entry, dict) and 'name' in entry:
                traits.append({
                    'name': entry.get('name'),
                    'entries': entry.get('entries', [])
                })
                
        return traits
        
    def scrape_feats(self) -> List[Dict]:
        """Scrape all feat data."""
        self.log("Scraping feats...")
        
        url = f"{self.GITHUB_RAW_URL}/feats.json"
        data = self.fetch_json(url)
        
        feats_data = []
        if data and 'feat' in data:
            for feat in tqdm(data['feat'], desc="Processing feats"):
                feat_info = {
                    'name': feat.get('name'),
                    'source': feat.get('source'),
                    'description': feat.get('entries', []),
                    'prerequisites': feat.get('prerequisite', []),
                    'ability_score_increase': feat.get('ability', []),
                    'repeatable': feat.get('repeatable', False),
                    'category': feat.get('category', 'general')  # origin, general, etc.
                }
                feats_data.append(feat_info)
                
        self.save_json(feats_data, "feats.json")
        return feats_data
        
    def scrape_spells(self) -> List[Dict]:
        """Scrape all spell data."""
        self.log("Scraping spells...")
        
        url = f"{self.GITHUB_RAW_URL}/spells/spells-phb.json"
        data = self.fetch_json(url)
        
        spells_data = []
        if data and 'spell' in data:
            for spell in tqdm(data['spell'], desc="Processing spells"):
                spell_info = {
                    'name': spell.get('name'),
                    'source': spell.get('source'),
                    'level': spell.get('level', 0),
                    'school': spell.get('school'),
                    'casting_time': spell.get('time', []),
                    'range': spell.get('range', {}),
                    'components': spell.get('components', {}),
                    'duration': spell.get('duration', []),
                    'description': spell.get('entries', []),
                    'higher_levels': spell.get('entriesHigherLevel', []),
                    'classes': self._extract_spell_classes(spell),
                    'concentration': spell.get('duration', [{}])[0].get('concentration', False) if spell.get('duration') else False,
                    'ritual': spell.get('ritual', False)
                }
                spells_data.append(spell_info)
                
        # Fetch additional spell sources
        additional_sources = [
            "spells-xge.json",
            "spells-tce.json",
            "spells-ftd.json"
        ]
        
        for source in additional_sources:
            url = f"{self.GITHUB_RAW_URL}/spells/{source}"
            data = self.fetch_json(url)
            if data and 'spell' in data:
                for spell in data['spell']:
                    spell_info = {
                        'name': spell.get('name'),
                        'source': spell.get('source'),
                        'level': spell.get('level', 0),
                        'school': spell.get('school'),
                        'casting_time': spell.get('time', []),
                        'range': spell.get('range', {}),
                        'components': spell.get('components', {}),
                        'duration': spell.get('duration', []),
                        'description': spell.get('entries', []),
                        'higher_levels': spell.get('entriesHigherLevel', []),
                        'classes': self._extract_spell_classes(spell),
                        'concentration': spell.get('duration', [{}])[0].get('concentration', False) if spell.get('duration') else False,
                        'ritual': spell.get('ritual', False)
                    }
                    spells_data.append(spell_info)
                    
        self.save_json(spells_data, "spells.json")
        return spells_data
        
    def _extract_spell_classes(self, spell: Dict) -> List[str]:
        """Extract which classes can cast this spell."""
        classes = []
        class_data = spell.get('classes', {})
        
        if 'fromClassList' in class_data:
            for cls in class_data['fromClassList']:
                if isinstance(cls, dict):
                    classes.append(cls.get('name', ''))
                elif isinstance(cls, str):
                    classes.append(cls)
                    
        return classes
        
    def scrape_equipment(self) -> List[Dict]:
        """Scrape all equipment data."""
        self.log("Scraping equipment...")
        
        url = f"{self.GITHUB_RAW_URL}/items.json"
        data = self.fetch_json(url)
        
        equipment_data = []
        if data and 'item' in data:
            for item in tqdm(data['item'], desc="Processing equipment"):
                equipment_info = {
                    'name': item.get('name'),
                    'source': item.get('source'),
                    'type': item.get('type'),
                    'rarity': item.get('rarity', 'none'),
                    'value': item.get('value'),
                    'weight': item.get('weight'),
                    'description': item.get('entries', []),
                    'properties': item.get('property', []),
                    # Weapon-specific
                    'weapon_category': item.get('weaponCategory'),
                    'damage': item.get('dmg1'),
                    'damage_type': item.get('dmgType'),
                    'range': item.get('range'),
                    # Armor-specific
                    'armor_class': item.get('ac'),
                    'armor_type': item.get('type') if item.get('type') in ['LA', 'MA', 'HA', 'S'] else None,
                    'strength_requirement': item.get('strength'),
                    'stealth_disadvantage': item.get('stealth', False)
                }
                equipment_data.append(equipment_info)
                
        self.save_json(equipment_data, "equipment.json")
        return equipment_data
        
    def scrape_skills(self) -> List[Dict]:
        """Create skills data (standard D&D skills)."""
        self.log("Creating skills data...")
        
        skills_data = [
            {'name': 'Acrobatics', 'ability': 'dex', 'description': 'Stay on your feet in tricky situations'},
            {'name': 'Animal Handling', 'ability': 'wis', 'description': 'Calm or train animals'},
            {'name': 'Arcana', 'ability': 'int', 'description': 'Recall lore about spells, magic items, and the planes'},
            {'name': 'Athletics', 'ability': 'str', 'description': 'Climb, jump, swim, or perform other physical activities'},
            {'name': 'Deception', 'ability': 'cha', 'description': 'Convincingly hide the truth'},
            {'name': 'History', 'ability': 'int', 'description': 'Recall lore about historical events'},
            {'name': 'Insight', 'ability': 'wis', 'description': 'Determine the true intentions of a creature'},
            {'name': 'Intimidation', 'ability': 'cha', 'description': 'Influence others through threats'},
            {'name': 'Investigation', 'ability': 'int', 'description': 'Look around for clues and deduce conclusions'},
            {'name': 'Medicine', 'ability': 'wis', 'description': 'Diagnose illnesses and stabilize dying creatures'},
            {'name': 'Nature', 'ability': 'int', 'description': 'Recall lore about terrain, plants, animals, and weather'},
            {'name': 'Perception', 'ability': 'wis', 'description': 'Spot, hear, or otherwise detect the presence of something'},
            {'name': 'Performance', 'ability': 'cha', 'description': 'Delight an audience with music, dance, or other entertainment'},
            {'name': 'Persuasion', 'ability': 'cha', 'description': 'Influence others through charm or reason'},
            {'name': 'Religion', 'ability': 'int', 'description': 'Recall lore about deities and religious practices'},
            {'name': 'Sleight of Hand', 'ability': 'dex', 'description': 'Pick pockets, conceal objects, or perform tricks'},
            {'name': 'Stealth', 'ability': 'dex', 'description': 'Conceal yourself from enemies or sneak past them'},
            {'name': 'Survival', 'ability': 'wis', 'description': 'Track creatures, navigate wilderness, or find food'}
        ]
        
        self.save_json(skills_data, "skills.json")
        return skills_data
        
    def scrape_languages(self) -> List[Dict]:
        """Create languages data."""
        self.log("Creating languages data...")
        
        url = f"{self.GITHUB_RAW_URL}/languages.json"
        data = self.fetch_json(url)
        
        languages_data = []
        if data and 'language' in data:
            for lang in data['language']:
                language_info = {
                    'name': lang.get('name'),
                    'type': lang.get('type', 'standard'),
                    'script': lang.get('script'),
                    'typical_speakers': lang.get('typicalSpeakers', []),
                    'description': lang.get('entries', [])
                }
                languages_data.append(language_info)
        else:
            # Fallback to standard languages if API fails
            languages_data = [
                {'name': 'Common', 'type': 'standard', 'script': 'Common', 'typical_speakers': ['Humans']},
                {'name': 'Dwarvish', 'type': 'standard', 'script': 'Dwarvish', 'typical_speakers': ['Dwarves']},
                {'name': 'Elvish', 'type': 'standard', 'script': 'Elvish', 'typical_speakers': ['Elves']},
                {'name': 'Giant', 'type': 'standard', 'script': 'Dwarvish', 'typical_speakers': ['Ogres', 'Giants']},
                {'name': 'Gnomish', 'type': 'standard', 'script': 'Dwarvish', 'typical_speakers': ['Gnomes']},
                {'name': 'Goblin', 'type': 'standard', 'script': 'Dwarvish', 'typical_speakers': ['Goblinoids']},
                {'name': 'Halfling', 'type': 'standard', 'script': 'Common', 'typical_speakers': ['Halflings']},
                {'name': 'Orc', 'type': 'standard', 'script': 'Dwarvish', 'typical_speakers': ['Orcs']},
                {'name': 'Abyssal', 'type': 'exotic', 'script': 'Infernal', 'typical_speakers': ['Demons']},
                {'name': 'Celestial', 'type': 'exotic', 'script': 'Celestial', 'typical_speakers': ['Celestials']},
                {'name': 'Draconic', 'type': 'exotic', 'script': 'Draconic', 'typical_speakers': ['Dragons', 'Dragonborn']},
                {'name': 'Deep Speech', 'type': 'exotic', 'script': None, 'typical_speakers': ['Aberrations']},
                {'name': 'Infernal', 'type': 'exotic', 'script': 'Infernal', 'typical_speakers': ['Devils']},
                {'name': 'Primordial', 'type': 'exotic', 'script': 'Dwarvish', 'typical_speakers': ['Elementals']},
                {'name': 'Sylvan', 'type': 'exotic', 'script': 'Elvish', 'typical_speakers': ['Fey']},
                {'name': 'Undercommon', 'type': 'exotic', 'script': 'Elvish', 'typical_speakers': ['Underdark traders']}
            ]
            
        self.save_json(languages_data, "languages.json")
        return languages_data
        
    def scrape_all(self):
        """Scrape all data types."""
        self.log("=" * 60)
        self.log("Starting D&D 5e.tools data scraping")
        self.log("=" * 60)
        
        start_time = time.time()
        
        # Scrape all data types
        self.scrape_classes()
        self.scrape_backgrounds()
        self.scrape_races()
        self.scrape_feats()
        self.scrape_spells()
        self.scrape_equipment()
        self.scrape_skills()
        self.scrape_languages()
        
        elapsed = time.time() - start_time
        self.log("=" * 60)
        self.log(f"Scraping complete! Total time: {elapsed:.2f} seconds")
        self.log(f"Data saved to: {self.output_dir.absolute()}")
        self.log("=" * 60)
        
    def create_summary(self):
        """Create a summary of scraped data."""
        summary = {
            'scraped_at': datetime.now().isoformat(),
            'files': {}
        }
        
        for json_file in self.output_dir.glob("*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                summary['files'][json_file.name] = {
                    'count': len(data) if isinstance(data, list) else 1,
                    'size_kb': json_file.stat().st_size / 1024
                }
                
        self.save_json(summary, "_summary.json")
        
        self.log("\nData Summary:")
        self.log("-" * 40)
        for filename, info in summary['files'].items():
            if filename != "_summary.json":
                self.log(f"{filename}: {info['count']} items ({info['size_kb']:.2f} KB)")


def main():
    """Main execution function."""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║    D&D 5e.tools Data Scraper                          ║
    ║    For Character Creator Database Population          ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    # Create scraper instance
    scraper = FiveEToolsScraper(output_dir="dnd_data")
    
    # Scrape all data
    scraper.scrape_all()
    
    # Create summary
    scraper.create_summary()
    
    print("\n✅ All done! Check the 'dnd_data' directory for JSON files.")
    print("\nNext steps:")
    print("1. Review the JSON files for accuracy")
    print("2. Create Django management command to import this data")
    print("3. Map 2024 PHB changes (backgrounds with ASI and origin feats)")
    

if __name__ == "__main__":
    main()
