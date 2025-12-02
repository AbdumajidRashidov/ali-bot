import pandas as pd
import re
from typing import Dict, List, Optional
from categories.base import AnalysisCategory, CalculationMethod

class UniversalExcelProcessor:
    """
    Generic Excel processor that can handle any category type.
    Refactored from the original excel_processor.py to be more flexible.
    """

    @staticmethod
    def clean_amount(amount_str) -> Optional[float]:
        """
        Extract numeric value from amount string.
        Handles formats like: 1500$, $1500, 1,500$, 1752$+LUMPE

        Args:
            amount_str: Amount string or number

        Returns:
            Float value or None
        """
        if pd.isna(amount_str):
            return None

        # Convert to string
        amount_str = str(amount_str)

        # Remove all non-numeric characters except . and -
        cleaned = re.sub(r'[^\d.-]', '', amount_str)

        # Try to convert to float
        try:
            return float(cleaned) if cleaned else None
        except:
            return None

    @staticmethod
    def detect_week_markers(df: pd.DataFrame, broker_column: str) -> pd.Series:
        """
        Detect week markers in a DataFrame.
        Looks for rows like "Week 4", "Week 5", etc.

        Args:
            df: DataFrame
            broker_column: Name of the broker column

        Returns:
            Series with week labels for each row
        """
        current_week = "Before Week 1"
        week_list = []

        for idx, row in df.iterrows():
            broker_val = str(row[broker_column]).strip() if pd.notna(row[broker_column]) else ''

            # Check if this row is a week marker
            week_match = re.search(r'week\s*(\d+)', broker_val.lower())
            if week_match:
                current_week = f"Week {week_match.group(1)}"

            week_list.append(current_week)

        return pd.Series(week_list, index=df.index)

    @staticmethod
    def clean_dataframe(
        df: pd.DataFrame,
        entity_column: str,
        amount_columns: List[str]
    ) -> pd.DataFrame:
        """
        Clean and prepare DataFrame for analysis.

        Args:
            df: Raw DataFrame
            entity_column: Column with entity names
            amount_columns: Columns with amounts

        Returns:
            Cleaned DataFrame
        """
        # Select relevant columns
        cols_to_keep = [entity_column] + amount_columns
        df_clean = df[cols_to_keep].copy()

        # Remove rows with missing amounts
        df_clean = df_clean.dropna(subset=amount_columns, how='all')

        # Clean amounts
        for col in amount_columns:
            df_clean[col] = df_clean[col].apply(UniversalExcelProcessor.clean_amount)

        # Remove rows where amounts couldn't be converted
        df_clean = df_clean.dropna(subset=amount_columns, how='all')

        # Remove rows with zero or negative amounts
        for col in amount_columns:
            df_clean = df_clean[df_clean[col] > 0]

        # Normalize entity names
        df_clean[entity_column] = df_clean[entity_column].astype(str).str.strip()

        # Remove rows with empty entity names or 'nan' string
        df_clean = df_clean[df_clean[entity_column] != 'nan']
        df_clean = df_clean[df_clean[entity_column] != '']

        return df_clean

    @staticmethod
    def process_category(
        df: pd.DataFrame,
        category: AnalysisCategory,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Process Excel data for a specific category.

        Args:
            df: pandas DataFrame
            category: AnalysisCategory instance
            config: Configuration dictionary (entity -> config)

        Returns:
            Results dictionary with structure:
            {
                'weeks': {week_name: {entity: {total_amount, percentage, earnings}}},
                'overall': {entity: {total_amount, percentage, earnings}}
            }
        """
        # Normalize column names
        df.columns = df.columns.str.strip()

        # Find broker column for week detection
        broker_col = None
        for col in df.columns:
            if 'broker' in col.lower():
                broker_col = col
                break

        # Add week detection if we have a broker column
        if broker_col and category.grouping_columns:
            df = df.copy()
            df['Week'] = UniversalExcelProcessor.detect_week_markers(df, broker_col)
            if 'Week' not in category.grouping_columns:
                category.grouping_columns.append('Week')

        # Clean the DataFrame (preserve grouping columns)
        cols_for_cleaning = [category.entity_column] + category.amount_columns
        if category.grouping_columns and 'Week' in df.columns:
            cols_for_cleaning = cols_for_cleaning + category.grouping_columns

        df_clean = UniversalExcelProcessor.clean_dataframe(
            df,
            category.entity_column,
            category.amount_columns
        )

        # Re-add Week column if it was removed
        if category.grouping_columns and 'Week' in df.columns and 'Week' not in df_clean.columns:
            # Map week back using index
            df_clean['Week'] = df.loc[df_clean.index, 'Week'].values

        # If we have grouping columns, process by groups
        if category.grouping_columns:
            return UniversalExcelProcessor._process_with_grouping(
                df_clean, category, config
            )
        else:
            return UniversalExcelProcessor._process_without_grouping(
                df_clean, category, config
            )

    @staticmethod
    def _process_with_grouping(
        df: pd.DataFrame,
        category: AnalysisCategory,
        config: Optional[Dict]
    ) -> Dict:
        """Process data with grouping (e.g., by week)"""
        entity_col = category.entity_column
        amount_col = category.amount_columns[0]  # Use first amount column

        # Group by week and entity
        group_cols = category.grouping_columns + [entity_col]
        weekly_data = df.groupby(group_cols)[amount_col].sum().reset_index()

        # Get unique weeks
        week_col = category.grouping_columns[0]
        weeks = weekly_data[week_col].unique()

        results = {
            'weeks': {},
            'overall': {}
        }

        # Process each week
        for week in weeks:
            week_df = weekly_data[weekly_data[week_col] == week]
            week_results = {}

            for _, row in week_df.iterrows():
                entity = row[entity_col]
                total_amount = row[amount_col]

                # Calculate earnings based on config
                earnings_data = UniversalExcelProcessor._calculate_earnings(
                    entity, total_amount, category, config
                )

                week_results[earnings_data['entity_name']] = earnings_data

            # Add entities from config that weren't in this week
            if config:
                for config_entity in config.keys():
                    if config_entity not in week_results:
                        week_results[config_entity] = {
                            'total_amount': 0,
                            'percentage': config[config_entity].get('value', 0),
                            'earnings': 0
                        }

            results['weeks'][week] = week_results

        # Calculate overall totals
        overall_totals = df.groupby(entity_col)[amount_col].sum().to_dict()

        for entity, total_amount in overall_totals.items():
            earnings_data = UniversalExcelProcessor._calculate_earnings(
                entity, total_amount, category, config
            )
            results['overall'][earnings_data['entity_name']] = earnings_data

        # Add entities from config that weren't in the file
        if config:
            for config_entity in config.keys():
                if config_entity not in results['overall']:
                    results['overall'][config_entity] = {
                        'total_amount': 0,
                        'percentage': config[config_entity].get('value', 0),
                        'earnings': 0
                    }

        return results

    @staticmethod
    def _process_without_grouping(
        df: pd.DataFrame,
        category: AnalysisCategory,
        config: Optional[Dict]
    ) -> Dict:
        """Process data without grouping"""
        entity_col = category.entity_column
        amount_col = category.amount_columns[0]

        # Group by entity
        entity_totals = df.groupby(entity_col)[amount_col].sum().to_dict()

        results = {'overall': {}}

        for entity, total_amount in entity_totals.items():
            earnings_data = UniversalExcelProcessor._calculate_earnings(
                entity, total_amount, category, config
            )
            results['overall'][earnings_data['entity_name']] = earnings_data

        # Add entities from config that weren't in the file
        if config:
            for config_entity in config.keys():
                if config_entity not in results['overall']:
                    results['overall'][config_entity] = {
                        'total_amount': 0,
                        'percentage': config[config_entity].get('value', 0),
                        'earnings': 0
                    }

        return results

    @staticmethod
    def _calculate_earnings(
        entity: str,
        total_amount: float,
        category: AnalysisCategory,
        config: Optional[Dict]
    ) -> Dict:
        """
        Calculate earnings for an entity based on category and config.

        Args:
            entity: Entity name
            total_amount: Total amount for this entity
            category: Analysis category
            config: Configuration

        Returns:
            Dict with total_amount, percentage/rate, and earnings
        """
        # Try to find matching config (case-insensitive)
        entity_config = None
        matched_name = entity

        if config:
            for config_entity, config_data in config.items():
                if entity.lower() == config_entity.lower():
                    entity_config = config_data
                    matched_name = config_entity
                    break

        # Calculate based on method
        if category.calculation_method == CalculationMethod.SUM_ONLY:
            return {
                'entity_name': matched_name,
                'total_amount': total_amount,
                'percentage': 0,
                'earnings': total_amount  # For sum_only, earnings = total
            }

        elif category.calculation_method == CalculationMethod.PERCENTAGE:
            percentage = entity_config.get('value', 0) if entity_config else 0
            earnings = (total_amount * percentage) / 100

            return {
                'entity_name': matched_name,
                'total_amount': total_amount,
                'percentage': percentage,
                'earnings': earnings
            }

        elif category.calculation_method == CalculationMethod.FLAT_RATE:
            flat_rate = entity_config.get('value', 0) if entity_config else 0

            return {
                'entity_name': matched_name,
                'total_amount': total_amount,
                'flat_rate': flat_rate,
                'earnings': flat_rate
            }

        else:  # CUSTOM or unknown
            return {
                'entity_name': matched_name,
                'total_amount': total_amount,
                'earnings': 0
            }
