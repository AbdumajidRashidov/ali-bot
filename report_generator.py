from typing import Dict, List, Optional
from categories.base import AnalysisCategory, CalculationMethod

class ReportGenerator:
    """
    Generate formatted reports for any category type.
    Supports weekly breakdowns and overall summaries.
    """

    @staticmethod
    def generate_analysis_report(
        category: AnalysisCategory,
        results: Dict,
        file_name: str
    ) -> List[str]:
        """
        Generate complete report for an analysis.

        Args:
            category: Analysis category
            results: Results from UniversalExcelProcessor
            file_name: Name of the Excel file

        Returns:
            List of message strings (one per week + overall)
        """
        messages = []

        # Generate weekly reports if available
        if 'weeks' in results and results['weeks']:
            for week, week_data in results['weeks'].items():
                week_report = ReportGenerator._generate_week_report(
                    category, week, week_data
                )
                if week_report:  # Only add if there's data
                    messages.append(week_report)

        # Generate overall summary
        if 'overall' in results and results['overall']:
            overall_report = ReportGenerator._generate_overall_report(
                category, results['overall'], file_name
            )
            messages.append(overall_report)

        return messages

    @staticmethod
    def _generate_week_report(
        category: AnalysisCategory,
        week: str,
        week_data: Dict
    ) -> Optional[str]:
        """
        Generate report for a single week.

        Args:
            category: Analysis category
            week: Week identifier
            week_data: Data for this week

        Returns:
            Formatted report string or None if no data
        """
        # Calculate totals
        week_total_revenue = 0
        week_total_earnings = 0

        for entity_data in week_data.values():
            week_total_revenue += entity_data.get('total_amount', 0)
            week_total_earnings += entity_data.get('earnings', 0)

        # Skip if no revenue
        if week_total_revenue == 0:
            return None

        # Build report
        report = f"📅 **{week}**\n\n"

        # Sort entities by revenue (descending)
        sorted_entities = sorted(
            week_data.items(),
            key=lambda x: x[1].get('total_amount', 0),
            reverse=True
        )

        for entity_name, data in sorted_entities:
            total_amount = data.get('total_amount', 0)

            # Skip entities with no revenue
            if total_amount == 0:
                continue

            report += ReportGenerator._format_entity_line(
                entity_name, data, category
            )

        # Add week summary
        report += f"\n─────────────────\n"
        report += f"Week Total: ${week_total_revenue:,.2f}\n"

        if category.calculation_method != CalculationMethod.SUM_ONLY:
            report += f"Week Earnings: ${week_total_earnings:,.2f}\n"

        return report

    @staticmethod
    def _generate_overall_report(
        category: AnalysisCategory,
        overall_data: Dict,
        file_name: str
    ) -> str:
        """
        Generate overall summary report.

        Args:
            category: Analysis category
            overall_data: Overall totals
            file_name: Excel file name

        Returns:
            Formatted report string
        """
        # Calculate grand totals
        grand_total_revenue = 0
        grand_total_earnings = 0

        for entity_data in overall_data.values():
            grand_total_revenue += entity_data.get('total_amount', 0)
            grand_total_earnings += entity_data.get('earnings', 0)

        # Build report
        report = f"📊 **{category.name} - {file_name}**\n\n"

        # Sort entities by revenue (descending)
        sorted_entities = sorted(
            overall_data.items(),
            key=lambda x: x[1].get('total_amount', 0),
            reverse=True
        )

        for entity_name, data in sorted_entities:
            total_amount = data.get('total_amount', 0)

            # Show all entities (even with 0) in overall report
            report += ReportGenerator._format_entity_line(
                entity_name, data, category, show_zero=True
            )

        # Add grand summary
        report += f"\n═══════════════════\n"
        report += f"📈 Total Revenue: ${grand_total_revenue:,.2f}\n"

        if category.calculation_method != CalculationMethod.SUM_ONLY:
            report += f"💰 Total Earnings: ${grand_total_earnings:,.2f}\n"

        return report

    @staticmethod
    def _format_entity_line(
        entity_name: str,
        data: Dict,
        category: AnalysisCategory,
        show_zero: bool = False
    ) -> str:
        """
        Format a single entity line for the report.

        Args:
            entity_name: Name of entity
            data: Entity data
            category: Analysis category
            show_zero: Whether to show entities with zero amounts

        Returns:
            Formatted line string
        """
        total_amount = data.get('total_amount', 0)

        # Skip zero amounts unless explicitly showing them
        if not show_zero and total_amount == 0:
            return ""

        line = f"👤 **{entity_name}**\n"
        line += f"   Revenue: ${total_amount:,.2f}\n"

        # Add calculation-specific info
        if category.calculation_method == CalculationMethod.PERCENTAGE:
            percentage = data.get('percentage', 0)
            earnings = data.get('earnings', 0)
            line += f"   Percentage: {percentage}%\n"
            line += f"   Earnings: ${earnings:,.2f}\n"

        elif category.calculation_method == CalculationMethod.FLAT_RATE:
            flat_rate = data.get('flat_rate', 0)
            earnings = data.get('earnings', 0)
            line += f"   Flat Rate: ${flat_rate:,.2f}\n"
            line += f"   Earnings: ${earnings:,.2f}\n"

        # For SUM_ONLY, just show revenue (no earnings calculation)

        line += "\n"
        return line

    @staticmethod
    def generate_category_selection_menu(categories: List[Dict]) -> str:
        """
        Generate a menu for category selection.

        Args:
            categories: List of detected category dicts

        Returns:
            Formatted menu string
        """
        if not categories:
            return "❌ No analysis categories detected in this file."

        menu = "📊 **Analysis Options Detected:**\n\n"

        for i, cat in enumerate(categories, 1):
            emoji = ReportGenerator._get_category_emoji(cat['name'])
            menu += f"{i}️⃣ {emoji} **{cat['name']}**\n"
            menu += f"   {cat['description']}\n"

            # Show confidence if available
            if 'confidence' in cat and cat['confidence'] < 1.0:
                menu += f"   (Confidence: {cat['confidence']*100:.0f}%)\n"

            menu += "\n"

        menu += "━━━━━━━━━━━━━━━━━━\n"
        menu += "**How to proceed:**\n"
        menu += "• Select specific: `/analyze 1 2`\n"
        menu += "• Run all: `/analyze all`\n"
        menu += "• Cancel: `/cancel`\n"

        return menu

    @staticmethod
    def _get_category_emoji(category_name: str) -> str:
        """Get emoji for category name"""
        name_lower = category_name.lower()

        if 'dispatch' in name_lower:
            return "📋"
        elif 'driver' in name_lower:
            return "🚗"
        elif 'broker' in name_lower:
            return "🏢"
        elif 'equipment' in name_lower:
            return "🚚"
        elif 'route' in name_lower:
            return "🗺️"
        else:
            return "📊"

    @staticmethod
    def generate_config_needed_message(
        category: AnalysisCategory,
        entities: List[str],
        ai_suggestion: Optional[Dict] = None
    ) -> str:
        """
        Generate message when configuration is needed.

        Args:
            category: Analysis category
            entities: List of entities found
            ai_suggestion: Optional AI suggestion for config

        Returns:
            Formatted message
        """
        emoji = ReportGenerator._get_category_emoji(category.name)
        message = f"{emoji} **Configuration Needed: {category.name}**\n\n"

        # Show AI suggestion if available
        if ai_suggestion:
            message += f"💡 **AI Recommendation:**\n"
            message += f"Method: {ai_suggestion.get('method', 'percentage').title()}\n"
            message += f"Reason: {ai_suggestion.get('reasoning', 'Based on data analysis')}\n\n"
            message += "Accept AI suggestion? Reply:\n"
            message += "• `yes` - Use recommended method\n"
            message += "• `custom` - I'll configure manually\n"
        else:
            # No AI suggestion, go straight to config
            message += category.get_config_prompt(entities)

        return message

    @staticmethod
    def generate_error_message(error: Exception) -> str:
        """
        Generate user-friendly error message.

        Args:
            error: Exception that occurred

        Returns:
            Formatted error message
        """
        error_msg = f"❌ **Error Processing File**\n\n"
        error_msg += f"Details: {str(error)}\n\n"
        error_msg += "Please check:\n"
        error_msg += "• File format is .xlsx or .xls\n"
        error_msg += "• File contains data rows\n"
        error_msg += "• Column names are clear\n\n"
        error_msg += "Need help? Send /start for instructions."

        return error_msg

    @staticmethod
    def generate_analysis_summary(categories: List[Dict], results_count: int) -> str:
        """
        Generate summary after analyses complete.

        Args:
            categories: Categories that were analyzed
            results_count: Number of result messages sent

        Returns:
            Summary message
        """
        summary = f"✅ **Analysis Complete!**\n\n"
        summary += f"Ran {len(categories)} analysis type(s):\n"

        for cat in categories:
            emoji = ReportGenerator._get_category_emoji(cat['name'])
            summary += f"• {emoji} {cat['name']}\n"

        summary += f"\nSent {results_count} report message(s).\n"

        return summary
