import pandas as pd
import re
from typing import Dict

def process_excel_file(file_path: str, dispatcher_percentages: Dict[str, float]) -> Dict:
    """
    Process Excel file and calculate earnings for each dispatcher, grouped by week.

    Args:
        file_path: Path to the Excel file
        dispatcher_percentages: Dictionary mapping dispatcher names to their percentages

    Returns:
        Dictionary with weekly dispatcher earnings information
    """
    # Read the Excel file
    df = pd.read_excel(file_path)

    # Normalize column names (remove extra spaces, make lowercase for comparison)
    df.columns = df.columns.str.strip()

    # Find the dispatch, amount, and broker columns (case-insensitive)
    dispatch_col = None
    amount_col = None
    broker_col = None

    for col in df.columns:
        col_lower = col.lower()
        if 'dispatch' in col_lower:
            dispatch_col = col
        if 'amount' in col_lower or 'total' in col_lower or 'revenue' in col_lower:
            amount_col = col
        if 'broker' in col_lower:
            broker_col = col

    if dispatch_col is None:
        raise ValueError("Could not find 'Dispatch' column in Excel file")
    if amount_col is None:
        raise ValueError("Could not find 'Amount' or 'Total' column in Excel file")
    if broker_col is None:
        raise ValueError("Could not find 'Broker' column in Excel file")

    # Add a week identifier column by detecting week markers
    current_week = "Before Week 1"
    week_list = []

    for idx, row in df.iterrows():
        broker_val = str(row[broker_col]).strip() if pd.notna(row[broker_col]) else ''

        # Check if this row is a week marker (contains "week" followed by a number)
        week_match = re.search(r'week\s*(\d+)', broker_val.lower())
        if week_match:
            current_week = f"Week {week_match.group(1)}"

        week_list.append(current_week)

    df['Week'] = week_list

    # Clean the data - keep broker, dispatch, amount, and week
    df = df[[broker_col, dispatch_col, amount_col, 'Week']].copy()

    # Remove rows with missing amount
    df = df.dropna(subset=[amount_col])

    # Clean and convert amounts to numeric
    def clean_amount(amount_str):
        """Extract numeric value from amount string"""
        if pd.isna(amount_str):
            return None

        # Convert to string
        amount_str = str(amount_str)

        # Remove all non-numeric characters except . and -
        # This handles formats like: 1500$, $1500, 1,500$, 1752$+LUMPE
        cleaned = re.sub(r'[^\d.-]', '', amount_str)

        # Try to convert to float
        try:
            return float(cleaned) if cleaned else None
        except:
            return None

    df[amount_col] = df[amount_col].apply(clean_amount)

    # Remove rows where amount couldn't be converted to number
    df = df.dropna(subset=[amount_col])

    # Remove rows with zero or negative amounts
    df = df[df[amount_col] > 0]

    # Normalize dispatcher names (strip whitespace)
    df[dispatch_col] = df[dispatch_col].astype(str).str.strip()

    # Remove rows with empty dispatcher names or 'nan' string
    df = df[df[dispatch_col] != 'nan']
    df = df[df[dispatch_col] != '']

    # Group by week and dispatcher, then sum amounts
    weekly_data = df.groupby(['Week', dispatch_col])[amount_col].sum().reset_index()

    # Get unique weeks in order
    weeks = weekly_data['Week'].unique()

    # Build results structure: {week: {dispatcher: {...}}}
    results = {
        'weeks': {},
        'overall': {}
    }

    # Process each week
    for week in weeks:
        week_df = weekly_data[weekly_data['Week'] == week]
        week_results = {}

        for _, row in week_df.iterrows():
            dispatcher = row[dispatch_col]
            total_amount = row[amount_col]

            # Try to find matching percentage (case-insensitive)
            percentage = None
            matched_name = None

            for config_dispatcher, config_percentage in dispatcher_percentages.items():
                if dispatcher.lower() == config_dispatcher.lower():
                    percentage = config_percentage
                    matched_name = config_dispatcher
                    break

            if percentage is None:
                # Dispatcher not in config, use 0%
                percentage = 0
                matched_name = dispatcher

            earnings = (total_amount * percentage) / 100

            week_results[matched_name] = {
                'total_amount': total_amount,
                'percentage': percentage,
                'earnings': earnings
            }

        # Add dispatchers from config that weren't in this week
        for config_dispatcher, config_percentage in dispatcher_percentages.items():
            found = False
            for result_dispatcher in week_results.keys():
                if result_dispatcher.lower() == config_dispatcher.lower():
                    found = True
                    break

            if not found:
                week_results[config_dispatcher] = {
                    'total_amount': 0,
                    'percentage': config_percentage,
                    'earnings': 0
                }

        results['weeks'][week] = week_results

    # Calculate overall totals across all weeks
    overall_totals = df.groupby(dispatch_col)[amount_col].sum().to_dict()

    for dispatcher, total_amount in overall_totals.items():
        # Try to find matching percentage (case-insensitive)
        percentage = None
        matched_name = None

        for config_dispatcher, config_percentage in dispatcher_percentages.items():
            if dispatcher.lower() == config_dispatcher.lower():
                percentage = config_percentage
                matched_name = config_dispatcher
                break

        if percentage is None:
            percentage = 0
            matched_name = dispatcher

        earnings = (total_amount * percentage) / 100

        results['overall'][matched_name] = {
            'total_amount': total_amount,
            'percentage': percentage,
            'earnings': earnings
        }

    # Add dispatchers from config that weren't in the file
    for config_dispatcher, config_percentage in dispatcher_percentages.items():
        found = False
        for result_dispatcher in results['overall'].keys():
            if result_dispatcher.lower() == config_dispatcher.lower():
                found = True
                break

        if not found:
            results['overall'][config_dispatcher] = {
                'total_amount': 0,
                'percentage': config_percentage,
                'earnings': 0
            }

    return results
