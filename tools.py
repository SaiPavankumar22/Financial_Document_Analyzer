## Importing libraries and files
import os
from dotenv import load_dotenv
from typing import Type
from pydantic import BaseModel, Field

from crewai.tools import BaseTool, tool
from crewai_tools import SerperDevTool

load_dotenv()

## Creating search tool
search_tool = SerperDevTool()


class FinancialDocumentInput(BaseModel):
    """Schema for providing path to a financial document (PDF)."""
    path: str = Field(
        default='data/sample.pdf',
        description="Path to the PDF file containing financial data."
    )

## Creating custom pdf reader tool
class _FinancialDocumentTool(BaseTool):
    name: str = "Financial Document Reader"
    description: str = (
        "Reads financial PDF reports and extracts clean, structured text. "
        "This tool ensures formatting consistency and removes noisy whitespace, "
        "so that downstream analysis tools can work on accurate content."
    )
    args_schema: Type[BaseModel] = FinancialDocumentInput

    def _run(self, path: str = 'data/sample.pdf') -> str:
        """Read and clean text from financial PDF documents.

        Args:
            path (str): Path of the PDF file. Defaults to 'data/sample.pdf'.

        Returns:
            str: Extracted and cleaned text content from the financial document.
        """
        try:
            from langchain.document_loaders import PyPDFLoader as Pdf
            docs = Pdf(file_path=path).load()

            full_report = ""
            for data in docs:
                content = data.page_content.strip()

                # Remove excess whitespace and normalize
                while "\n\n" in content:
                    content = content.replace("\n\n", "\n")

                full_report += content + "\n"

            cleaned_report = full_report.strip()
            if not cleaned_report:
                return "Error: Uploaded PDF contains no readable text."

            return cleaned_report

        except Exception as e:
            return f"Error reading PDF file: {str(e)}"

## Creating Investment Analysis Tool
@tool("Investment Analysis Tool")
def analyze_investment_tool(financial_document_data: str) -> str:
    """Analyze extracted financial data to generate structured investment insights.

    The analysis includes:
    - Financial health assessment
    - Key financial metrics (revenue, margins, ratios)
    - Investment recommendations
    - Risk factors & mitigation
    """
    if not financial_document_data.strip():
        return "No financial data provided for analysis."

    processed_data = financial_document_data.replace("  ", " ")

    analysis_sections = [
        "=== INVESTMENT ANALYSIS REPORT ===",
        "",
        "1. FINANCIAL HEALTH ASSESSMENT:",
        "   - Document processed successfully",
        f"   - Content length: {len(processed_data)} characters",
        "",
        "2. KEY FINANCIAL METRICS:",
        "   - [Revenue, profitability, and debt ratios extracted here]",
        "",
        "3. INVESTMENT RECOMMENDATIONS:",
        "   - [Buy/Hold/Sell advice with rationale]",
        "",
        "4. RISK FACTORS:",
        "   - [Key business, operational, and market risks]",
        "",
        "Note: This is a template. Insert actual financial insights in production."
    ]
    return "\n".join(analysis_sections)

## Creating Risk Assessment Tool
@tool("Risk Assessment Tool")
def create_risk_assessment_tool(financial_document_data: str) -> str:
    """Perform detailed risk assessment from financial document data.

    The assessment includes:
    - Credit risk
    - Market/industry risk
    - Operational risks
    - Regulatory compliance
    - Overall rating
    """
    if not financial_document_data.strip():
        return "No financial data provided for risk assessment."

    risk_report = [
        "=== RISK ASSESSMENT REPORT ===",
        "",
        "1. CREDIT RISK ANALYSIS:",
        "   - [Debt levels, liquidity ratios, leverage]",
        "",
        "2. MARKET RISK FACTORS:",
        "   - [Volatility, industry exposure, macroeconomic risks]",
        "",
        "3. OPERATIONAL RISKS:",
        "   - [Business model risks, efficiency bottlenecks]",
        "",
        "4. REGULATORY COMPLIANCE:",
        "   - [Legal, compliance, and governance risks]",
        "",
        "5. OVERALL RISK RATING:",
        "   - [Low/Medium/High risk with explanation]",
        "",
        "Note: Replace placeholders with actual computed risk analysis."
    ]
    return "\n".join(risk_report)


class FinancialDocumentTool:
    """Wrapper for compatibility with existing code expecting FinancialDocumentTool.read_data_tool."""

    @staticmethod
    def read_data_tool(path: str = 'data/sample.pdf') -> str:
        """Static wrapper method to read financial documents cleanly."""
        tool_instance = _FinancialDocumentTool()
        return tool_instance._run(path)
