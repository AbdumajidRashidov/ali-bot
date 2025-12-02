from typing import Dict, List
from .base import AnalysisCategory, CalculationMethod

class DriverAnalysis(AnalysisCategory):
    """Analysis category for driver payments/earnings"""

    def __init__(
        self,
        entity_column: str,
        amount_columns: List[str],
        grouping_columns: List[str] = None,
        confidence: float = 1.0
    ):
        super().__init__(
            name="Driver Payments",
            entity_column=entity_column,
            amount_columns=amount_columns,
            grouping_columns=grouping_columns,
            calculation_method=CalculationMethod.PERCENTAGE,
            config_needed=True,
            description="Calculate payments for each driver based on their revenue",
            confidence=confidence
        )

    def get_config_prompt(self, entities: List[str]) -> str:
        """
        Get configuration prompt for driver payments.

        Args:
            entities: List of driver names

        Returns:
            Formatted prompt
        """
        prompt = "🚗 **Driver Payments Configuration**\n\n"
        prompt += "Please provide the payment percentage for each driver.\n"
        prompt += "Format: `DriverName: Percentage`\n\n"
        prompt += "Example:\n"

        # Show first few drivers as examples
        for i, driver in enumerate(entities[:3]):
            example_pct = 70.0 if i == 0 else 65.0
            prompt += f"{driver}: {example_pct}\n"

        if len(entities) > 3:
            prompt += f"... and {len(entities) - 3} more\n"

        prompt += "\nSend all percentages in one message."

        return prompt

    def validate_config(self, config: Dict) -> bool:
        """
        Validate driver configuration.

        Args:
            config: Dict mapping driver names to config dicts

        Returns:
            True if valid
        """
        if not config:
            return False

        for driver, settings in config.items():
            if not isinstance(settings, dict):
                return False

            if 'type' not in settings or 'value' not in settings:
                return False

            if settings['type'] not in ['percentage', 'flat_rate']:
                return False

            try:
                value = float(settings['value'])
                if value < 0:
                    return False
                if settings['type'] == 'percentage' and value > 100:
                    return False
            except (ValueError, TypeError):
                return False

        return True

    @classmethod
    def from_dict(cls, data: Dict) -> 'DriverAnalysis':
        """Create DriverAnalysis from dictionary"""
        return cls(
            entity_column=data['entity_column'],
            amount_columns=data['amount_columns'],
            grouping_columns=data.get('grouping_columns', []),
            confidence=data.get('confidence', 1.0)
        )
