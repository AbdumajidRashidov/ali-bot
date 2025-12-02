import json
import os
from typing import Dict, Optional, List
from categories.base import AnalysisCategory

class ConfigManager:
    """
    Manages configuration for multiple analysis categories.
    Stores configs in a JSON file with support for different calculation types.
    """

    def __init__(self, config_file: str = 'analysis_config.json'):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to JSON config file
        """
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self) -> Dict:
        """
        Load configuration from file.

        Returns:
            Configuration dictionary
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {self.config_file}, using empty config")
                return {}
        return {}

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get_category_config(self, category: AnalysisCategory) -> Optional[Dict]:
        """
        Get configuration for a specific category.

        Args:
            category: Analysis category

        Returns:
            Config dict or None if not configured
        """
        category_id = category.get_category_id()
        return self.config.get(category_id)

    def set_category_config(self, category: AnalysisCategory, config: Dict):
        """
        Set configuration for a category.

        Args:
            category: Analysis category
            config: Configuration dictionary
        """
        category_id = category.get_category_id()
        self.config[category_id] = config
        self.save_config()

    def has_category_config(self, category: AnalysisCategory) -> bool:
        """
        Check if a category has configuration.

        Args:
            category: Analysis category

        Returns:
            True if configured
        """
        category_id = category.get_category_id()
        return category_id in self.config and bool(self.config[category_id])

    def delete_category_config(self, category: AnalysisCategory):
        """
        Delete configuration for a category.

        Args:
            category: Analysis category
        """
        category_id = category.get_category_id()
        if category_id in self.config:
            del self.config[category_id]
            self.save_config()

    def get_all_categories(self) -> List[str]:
        """
        Get list of all configured category IDs.

        Returns:
            List of category IDs
        """
        return list(self.config.keys())

    def migrate_legacy_config(self, legacy_file: str = 'dispatcher_config.json'):
        """
        Migrate old dispatcher-only config to new multi-category format.

        Args:
            legacy_file: Path to old config file
        """
        if not os.path.exists(legacy_file):
            return

        try:
            with open(legacy_file, 'r') as f:
                legacy_config = json.load(f)

            # Convert to new format
            new_config = {}
            for dispatcher, percentage in legacy_config.items():
                new_config[dispatcher] = {
                    'type': 'percentage',
                    'value': percentage
                }

            # Save under dispatcher_earnings key
            self.config['dispatcher_earnings'] = new_config
            self.save_config()

            print(f"Migrated legacy config from {legacy_file}")

        except Exception as e:
            print(f"Error migrating legacy config: {e}")

    def parse_config_from_text(self, text: str, category: AnalysisCategory) -> Dict:
        """
        Parse configuration from user text input.

        Args:
            text: User input text (e.g., "Java: 1.5\\nBaxa: 1.3")
            category: Category being configured

        Returns:
            Parsed configuration dictionary
        """
        config = {}
        lines = text.strip().split('\n')

        for line in lines:
            if ':' not in line:
                continue

            parts = line.split(':', 1)
            entity_name = parts[0].strip()
            value_str = parts[1].strip()

            # Remove common symbols like %, $, commas
            value_str = value_str.replace('%', '').replace('$', '').replace(',', '').strip()

            try:
                value = float(value_str)

                # Determine type based on category's calculation method
                if category.calculation_method.value == 'percentage':
                    config[entity_name] = {
                        'type': 'percentage',
                        'value': value
                    }
                elif category.calculation_method.value == 'flat_rate':
                    config[entity_name] = {
                        'type': 'flat_rate',
                        'value': value
                    }
                else:
                    config[entity_name] = {
                        'type': 'value',
                        'value': value
                    }

            except ValueError:
                print(f"Warning: Could not parse value for {entity_name}: {value_str}")
                continue

        return config

    def format_config_for_display(self, category: AnalysisCategory) -> str:
        """
        Format category configuration for display to user.

        Args:
            category: Analysis category

        Returns:
            Formatted string
        """
        config = self.get_category_config(category)

        if not config:
            return f"No configuration found for {category.name}"

        output = f"📊 **{category.name} Configuration**\n\n"

        for entity, settings in sorted(config.items()):
            if settings['type'] == 'percentage':
                output += f"• {entity}: {settings['value']}%\n"
            elif settings['type'] == 'flat_rate':
                output += f"• {entity}: ${settings['value']:.2f}\n"
            else:
                output += f"• {entity}: {settings['value']}\n"

        return output

    def validate_and_save(self, category: AnalysisCategory, config: Dict) -> bool:
        """
        Validate and save configuration for a category.

        Args:
            category: Analysis category
            config: Configuration to validate and save

        Returns:
            True if valid and saved, False otherwise
        """
        if not category.validate_config(config):
            return False

        self.set_category_config(category, config)
        return True
