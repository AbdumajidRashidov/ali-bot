from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from enum import Enum

class CalculationMethod(Enum):
    """Types of calculation methods for earnings"""
    PERCENTAGE = "percentage"
    FLAT_RATE = "flat_rate"
    SUM_ONLY = "sum_only"
    CUSTOM = "custom"

class AnalysisCategory(ABC):
    """
    Base class for all analysis categories.
    Each category represents a type of analysis that can be performed on Excel data.
    """

    def __init__(
        self,
        name: str,
        entity_column: str,
        amount_columns: List[str],
        grouping_columns: Optional[List[str]] = None,
        calculation_method: CalculationMethod = CalculationMethod.PERCENTAGE,
        config_needed: bool = True,
        description: str = "",
        confidence: float = 1.0
    ):
        """
        Initialize an analysis category.

        Args:
            name: Display name of the category (e.g., "Dispatcher Earnings")
            entity_column: Column containing entity names (e.g., "Dispatch")
            amount_columns: Columns containing monetary amounts
            grouping_columns: Optional columns for grouping (e.g., ["Week"])
            calculation_method: How to calculate earnings
            config_needed: Whether this category needs configuration
            description: Human-readable description
            confidence: Confidence score from AI detection (0-1)
        """
        self.name = name
        self.entity_column = entity_column
        self.amount_columns = amount_columns
        self.grouping_columns = grouping_columns or []
        self.calculation_method = calculation_method
        self.config_needed = config_needed
        self.description = description
        self.confidence = confidence

    @abstractmethod
    def get_config_prompt(self, entities: List[str]) -> str:
        """
        Get a user-friendly prompt for configuring this category.

        Args:
            entities: List of unique entity names found in data

        Returns:
            Formatted prompt string
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict) -> bool:
        """
        Validate that configuration is correct for this category.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid, False otherwise
        """
        pass

    def get_category_id(self) -> str:
        """
        Get a unique identifier for this category (used for config storage).

        Returns:
            Lowercase, underscored identifier
        """
        return self.name.lower().replace(' ', '_')

    def to_dict(self) -> Dict:
        """
        Convert category to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            'name': self.name,
            'entity_column': self.entity_column,
            'amount_columns': self.amount_columns,
            'grouping_columns': self.grouping_columns,
            'calculation_method': self.calculation_method.value,
            'config_needed': self.config_needed,
            'description': self.description,
            'confidence': self.confidence
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'AnalysisCategory':
        """
        Create category from dictionary.

        Args:
            data: Dictionary with category data

        Returns:
            AnalysisCategory instance
        """
        # This should be overridden in subclasses for proper type creation
        calc_method = CalculationMethod(data.get('calculation_method', 'percentage'))
        return cls(
            name=data['name'],
            entity_column=data['entity_column'],
            amount_columns=data['amount_columns'],
            grouping_columns=data.get('grouping_columns', []),
            calculation_method=calc_method,
            config_needed=data.get('config_needed', True),
            description=data.get('description', ''),
            confidence=data.get('confidence', 1.0)
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', entity_column='{self.entity_column}')"
