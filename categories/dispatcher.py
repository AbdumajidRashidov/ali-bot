from typing import Dict, List
from .base import AnalysisCategory, CalculationMethod

class DispatcherAnalysis(AnalysisCategory):
    """Analysis category for dispatcher earnings"""

    def __init__(
        self,
        entity_column: str,
        amount_columns: List[str],
        grouping_columns: List[str] = None,
        confidence: float = 1.0
    ):
        super().__init__(
            name="Dispatcher Earnings",
            entity_column=entity_column,
            amount_columns=amount_columns,
            grouping_columns=grouping_columns,
            calculation_method=CalculationMethod.PERCENTAGE,
            config_needed=True,
            description="Calculate earnings for each dispatcher based on their revenue percentage",
            confidence=confidence
        )

    def get_config_prompt(self, entities: List[str]) -> str:
        """
        Get configuration prompt for dispatcher percentages.

        Args:
            entities: List of dispatcher names

        Returns:
            Formatted prompt
        """
        prompt = "📊 **Dispatcher Earnings Configuration**\n\n"
        prompt += "Please provide the earning percentage for each dispatcher.\n"
        prompt += "Format: `DispatcherName: Percentage`\n\n"
        prompt += "Example:\n"

        # Show first few dispatchers as examples
        for i, dispatcher in enumerate(entities[:3]):
            example_pct = 1.5 if i == 0 else 1.3
            prompt += f"{dispatcher}: {example_pct}\n"

        if len(entities) > 3:
            prompt += f"... and {len(entities) - 3} more\n"

        prompt += "\nSend all percentages in one message."

        return prompt

    def validate_config(self, config: Dict) -> bool:
        """
        Validate dispatcher configuration.

        Args:
            config: Dict mapping dispatcher names to config dicts

        Returns:
            True if valid
        """
        if not config:
            return False

        for dispatcher, settings in config.items():
            if not isinstance(settings, dict):
                return False

            if 'type' not in settings or 'value' not in settings:
                return False

            if settings['type'] != 'percentage':
                return False

            try:
                value = float(settings['value'])
                if value < 0 or value > 100:
                    return False
            except (ValueError, TypeError):
                return False

        return True

    @classmethod
    def from_dict(cls, data: Dict) -> 'DispatcherAnalysis':
        """Create DispatcherAnalysis from dictionary"""
        return cls(
            entity_column=data['entity_column'],
            amount_columns=data['amount_columns'],
            grouping_columns=data.get('grouping_columns', []),
            confidence=data.get('confidence', 1.0)
        )
