from typing import Dict, List
from .base import AnalysisCategory, CalculationMethod

class BrokerAnalysis(AnalysisCategory):
    """Analysis category for broker/customer performance"""

    def __init__(
        self,
        entity_column: str,
        amount_columns: List[str],
        grouping_columns: List[str] = None,
        confidence: float = 1.0
    ):
        super().__init__(
            name="Broker Performance",
            entity_column=entity_column,
            amount_columns=amount_columns,
            grouping_columns=grouping_columns,
            calculation_method=CalculationMethod.SUM_ONLY,
            config_needed=False,  # Just totals, no config needed
            description="Analyze revenue by broker/customer (totals only)",
            confidence=confidence
        )

    def get_config_prompt(self, entities: List[str]) -> str:
        """
        Broker analysis doesn't need configuration.

        Args:
            entities: List of broker names

        Returns:
            Empty string (no config needed)
        """
        return ""

    def validate_config(self, config: Dict) -> bool:
        """
        Broker analysis doesn't require configuration.

        Args:
            config: Config dict (not used)

        Returns:
            Always True
        """
        return True

    @classmethod
    def from_dict(cls, data: Dict) -> 'BrokerAnalysis':
        """Create BrokerAnalysis from dictionary"""
        return cls(
            entity_column=data['entity_column'],
            amount_columns=data['amount_columns'],
            grouping_columns=data.get('grouping_columns', []),
            confidence=data.get('confidence', 1.0)
        )
