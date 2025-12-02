import pandas as pd
import json
import os
from typing import Dict, List, Optional
from openai import OpenAI

class AIExcelAnalyzer:
    """
    Uses OpenAI GPT to intelligently analyze Excel file structure
    and detect possible analysis categories.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with OpenAI API key"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env file")
        self.client = OpenAI(api_key=self.api_key)

    def analyze_excel_structure(self, df: pd.DataFrame) -> Dict:
        """
        Analyze the structure of an Excel DataFrame.

        Args:
            df: pandas DataFrame from Excel file

        Returns:
            Dictionary with structure information
        """
        # Get column information
        columns = df.columns.tolist()

        # Get data types
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}

        # Get sample data (first 10 non-null rows)
        sample_data = {}
        for col in columns:
            non_null = df[col].dropna().head(10).tolist()
            sample_data[col] = [str(val) for val in non_null]

        # Get basic statistics
        stats = {
            'total_rows': len(df),
            'total_columns': len(columns),
            'column_names': columns
        }

        # Detect numeric columns
        numeric_cols = df.select_dtypes(include=['number', 'float64', 'int64']).columns.tolist()

        # Detect potential amount/money columns
        potential_amount_cols = [
            col for col in columns
            if any(keyword in col.lower() for keyword in ['amount', 'total', 'revenue', 'pay', 'earning', 'salary', 'rate'])
        ]

        # Detect potential name/entity columns
        potential_entity_cols = [
            col for col in columns
            if any(keyword in col.lower() for keyword in ['name', 'dispatch', 'driver', 'broker', 'customer', 'vendor'])
        ]

        structure = {
            'stats': stats,
            'dtypes': dtypes,
            'sample_data': sample_data,
            'numeric_columns': numeric_cols,
            'potential_amount_columns': potential_amount_cols,
            'potential_entity_columns': potential_entity_cols
        }

        return structure

    def detect_categories(self, structure: Dict) -> List[Dict]:
        """
        Use AI to detect possible analysis categories from the Excel structure.

        Args:
            structure: Excel structure from analyze_excel_structure()

        Returns:
            List of detected category dictionaries
        """
        # Prepare prompt for GPT
        prompt = self._build_detection_prompt(structure)

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at analyzing spreadsheet data structures.
                        Your job is to identify what types of analysis can be performed on the data.

                        Common categories include:
                        - Dispatcher Earnings: Revenue/earnings by dispatcher
                        - Driver Payments: Payments or earnings by driver
                        - Broker Performance: Revenue or metrics by broker/customer
                        - Equipment Analysis: Metrics by equipment/vehicle
                        - Route Analysis: Performance by route or destination

                        Return your analysis as a JSON object with this structure:
                        {
                            "categories": [
                                {
                                    "name": "Category Name",
                                    "entity_column": "column_name",
                                    "amount_columns": ["column1", "column2"],
                                    "description": "What this analysis shows",
                                    "confidence": 0.95
                                }
                            ]
                        }

                        Only include categories you're confident about (confidence > 0.7).
                        """
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get('categories', [])

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            # Fallback to rule-based detection
            return self._fallback_detection(structure)

    def suggest_calculation_method(self, category: Dict, structure: Dict) -> Dict:
        """
        Use AI to suggest how to calculate earnings for a category.

        Args:
            category: Detected category dictionary
            structure: Excel structure

        Returns:
            Dictionary with calculation suggestions
        """
        prompt = f"""
        I have a spreadsheet category: {category['name']}
        Entity column: {category['entity_column']}
        Amount columns: {category['amount_columns']}

        Sample data:
        {json.dumps(structure['sample_data'], indent=2)}

        Suggest the best calculation method for this category.
        Should each entity get:
        1. A percentage of their total amount?
        2. A flat rate per transaction?
        3. Just show totals (no earnings calculation)?
        4. Something else?

        Return JSON with:
        {{
            "method": "percentage" | "flat_rate" | "sum_only" | "custom",
            "reasoning": "Why this method is appropriate",
            "example": "Example calculation"
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst helping determine calculation methods for earnings analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"Error suggesting calculation: {e}")
            return {
                "method": "percentage",
                "reasoning": "Default to percentage-based calculation",
                "example": "Entity earns X% of their total revenue"
            }

    def _build_detection_prompt(self, structure: Dict) -> str:
        """Build a prompt for category detection"""
        prompt = f"""
        Analyze this spreadsheet structure and identify what analyses can be performed:

        Total rows: {structure['stats']['total_rows']}
        Total columns: {structure['stats']['total_columns']}

        Column names: {', '.join(structure['stats']['column_names'])}

        Numeric columns: {', '.join(structure['numeric_columns'])}

        Potential amount/money columns: {', '.join(structure['potential_amount_columns'])}

        Potential entity/name columns: {', '.join(structure['potential_entity_columns'])}

        Sample data (first few values per column):
        """

        # Add sample data for key columns
        for col in structure['potential_entity_columns'][:3]:  # Top 3 entity columns
            if col in structure['sample_data']:
                samples = structure['sample_data'][col][:5]
                prompt += f"\n  {col}: {', '.join(samples)}"

        for col in structure['potential_amount_columns'][:3]:  # Top 3 amount columns
            if col in structure['sample_data']:
                samples = structure['sample_data'][col][:5]
                prompt += f"\n  {col}: {', '.join(samples)}"

        return prompt

    def _fallback_detection(self, structure: Dict) -> List[Dict]:
        """
        Fallback rule-based detection when AI is unavailable.

        Args:
            structure: Excel structure

        Returns:
            List of detected categories
        """
        categories = []

        # Look for dispatcher column
        for col in structure['potential_entity_columns']:
            if 'dispatch' in col.lower():
                categories.append({
                    'name': 'Dispatcher Earnings',
                    'entity_column': col,
                    'amount_columns': structure['potential_amount_columns'][:1],
                    'description': 'Revenue and earnings by dispatcher',
                    'confidence': 0.8
                })

        # Look for driver column
        for col in structure['potential_entity_columns']:
            if 'driver' in col.lower():
                categories.append({
                    'name': 'Driver Payments',
                    'entity_column': col,
                    'amount_columns': structure['potential_amount_columns'][:1],
                    'description': 'Payments and earnings by driver',
                    'confidence': 0.8
                })

        # Look for broker/customer column
        for col in structure['potential_entity_columns']:
            if any(keyword in col.lower() for keyword in ['broker', 'customer', 'client']):
                categories.append({
                    'name': 'Broker Performance',
                    'entity_column': col,
                    'amount_columns': structure['potential_amount_columns'][:1],
                    'description': 'Revenue analysis by broker/customer',
                    'confidence': 0.8
                })

        return categories
