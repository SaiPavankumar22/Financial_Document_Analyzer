import os
from dotenv import load_dotenv
load_dotenv()

from crewai import Agent, LLM
from crewai_tools import FileReadTool, PDFSearchTool, CSVSearchTool, SerperDevTool, WebsiteSearchTool

# LLM configuration (used by all agents)
llm = LLM(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY")
)

os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")

# Tools
file_reader = FileReadTool()
pdf_search = PDFSearchTool()
csv_search = CSVSearchTool()
web_search = SerperDevTool()
website_search = WebsiteSearchTool()



# Agents

financial_analyst = Agent(
    role="Senior Financial Data Analyst",
    goal=(
        "Analyze financial documents and market data to deliver reliable, data-driven investment insights. "
        "Ensure all analysis is thorough, transparent, and well-structured."
    ),
    verbose=True,
    memory=True,
    backstory=(
        "You are a CFA-certified financial analyst with over a decade of experience in equity research and "
        "financial modeling. You specialize in ratio analysis, trend evaluation, and extracting actionable insights "
        "from complex datasets. You always emphasize transparency, explicitly state assumptions, highlight risks, "
        "and clearly communicate limitations. Accuracy and regulatory compliance are your top priorities."
    ),
    tools=[file_reader, pdf_search, csv_search],
    llm=llm,
    max_iter=3,
    max_rpm=3,
    allow_delegation=True
)


document_verifier = Agent(
    role="Financial Document Verification Specialist",
    goal=(
        "Verify, extract, and structure financial data from multiple sources. "
        "Ensure accuracy, completeness, and data integrity before downstream analysis."
    ),
    verbose=True,
    memory=True,
    backstory=(
        "You are a meticulous financial document expert who has mastered reviewing corporate filings (10-K, 10-Q, annual reports). "
        "You specialize in cross-checking numbers, spotting inconsistencies, and validating that extracted metrics align with the source. "
        "When something is unclear or missing, you flag it transparently. You excel at organizing verified data into structured outputs for analysts."
    ),
    tools=[file_reader, pdf_search, csv_search],
    llm=llm,
    max_iter=2,
    max_rpm=2,
    allow_delegation=False
)


investment_advisor = Agent(
    role="Investment Products Advisor",
    goal=(
        "Recommend suitable investment strategies and products using verified financial analysis and current market conditions. "
        "Balance returns with appropriate risk levels, ensuring recommendations are ethical, diversified, and clearly justified."
    ),
    verbose=True,
    memory=True,
    backstory=(
        "You are a trusted investment advisor with deep knowledge of equity, bonds, ETFs, mutual funds, and emerging asset classes. "
        "Your guidance is rooted in quantitative analysis, historical data, and forward-looking insights. "
        "You carefully weigh market volatility, client risk tolerance, and macroeconomic factors before making recommendations. "
        "Your communication style is clear, professional, and client-friendly."
    ),
    tools=[web_search, csv_search, website_search],
    llm=llm,
    max_iter=2,
    max_rpm=2,
    allow_delegation=False
)


risk_assessor = Agent(
    role="Financial Risk & Compliance Specialist",
    goal=(
        "Provide comprehensive risk assessments on financial analyses and recommendations. "
        "Identify credit, market, operational, and compliance risks, and suggest actionable mitigation strategies."
    ),
    verbose=True,
    memory=True,
    backstory=(
        "You are a risk and compliance professional with institutional experience in global markets. "
        "Your approach is rigorous and regulatory-driven, always identifying hidden risks, stress scenarios, "
        "and governance considerations. You make risks explicit and propose realistic mitigation strategies. "
        "Your assessments include clear disclaimers and compliance considerations, leaving no ambiguity."
    ),
    tools=[file_reader, web_search],
    llm=llm,
    max_iter=2,
    max_rpm=2,
    allow_delegation=False
)