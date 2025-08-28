## Importing libraries and files
from crewai import Task
from agents import financial_analyst, document_verifier, investment_advisor, risk_assessor
from tools import search_tool, FinancialDocumentTool

# Instantiate tools
financial_document_tool = FinancialDocumentTool()
search = search_tool

# Document Verification Task
verification = Task(
    description="""
    You are responsible for verifying the authenticity and quality of financial documents provided for analysis: {query}.
    
    Your job:
    1. Identify the type of documents (10-K, 10-Q, annual report, etc.)
    2. Check document integrity and authenticity
    3. Extract and organize all key financial data
    4. Cross-check figures across documents for consistency
    5. Flag any missing, incomplete, or suspicious data
    6. Confirm whether documents are ready for downstream analysis
    
    Be highly systematic, precise, and transparent in your verification.
    
    Use the document text provided: {document_text}
    """,
    expected_output="""
    A structured **Document Verification Report** containing:
    - Document classification (type, year, source)
    - Extracted financial metrics summary
    - Data consistency check results
    - Missing or incomplete data list
    - Reliability rating of documents
    - Recommendations for additional docs if needed
    - Data packaged in a format ready for analysis
    """,
    agent=document_verifier,
    tools=[financial_document_tool],
    async_execution=False,
)

# Financial Analysis Task
analyze_financial_document = Task(
    description="""
    You are a senior financial analyst. Analyze the provided financial documents to answer the user's query: {query}.
    
    Use the document text provided: {document_text}
    
    Your job:
    1. Extract and interpret key metrics (revenue, margins, liquidity, leverage ratios)
    2. Identify performance trends and growth/decline patterns
    3. Evaluate operational efficiency and profitability drivers
    4. Compare performance against industry benchmarks (if available)
    5. Highlight unusual or noteworthy financial events
    
    Stay objective and rely only on verified data from documents. If certain data is missing, clearly state limitations.
    """,
    expected_output="""
    A structured **Financial Analysis Report** containing:
    - Executive summary with key insights
    - Financial metrics breakdown with explanations
    - Trend and variance analysis
    - Strengths vs. weaknesses of the company
    - Benchmarking observations (if available)
    - Clear conclusions based on evidence
    - Explicit list of assumptions and limitations
    """,
    agent=financial_analyst,
    tools=[financial_document_tool, search],
    context=[verification],
    async_execution=False,
)

# Investment Analysis Task
investment_analysis = Task(
    description="""
    You are an experienced investment advisor. Based on the financial analysis, provide actionable investment recommendations for: {query}.
    
    Your job:
    1. Formulate an investment thesis based on financial performance
    2. Suggest investment vehicles (equities, ETFs, bonds, mutual funds, etc.)
    3. Tailor recommendations for different risk profiles:
       - Conservative
       - Moderate
       - Aggressive
    4. Consider current market outlook and sector trends
    5. Provide rationale linking financial data to strategy
    6. Ensure compliance with ethical and regulatory standards
    
    Always be transparent about risks and provide balanced reasoning.
    """,
    expected_output="""
    A structured **Investment Recommendations Report** containing:
    - Investment thesis summary
    - Specific recommended products/strategies
    - Rationale grounded in financial data and market context
    - Risk-return tradeoff for each recommendation
    - Portfolio allocation guidance (if applicable)
    - Relevant disclosures and disclaimers
    - Key external factors to monitor
    """,
    agent=investment_advisor,
    tools=[search],
    context=[analyze_financial_document],
    async_execution=False,
)

# Risk Assessment Task
risk_assessment = Task(
    description="""
    You are a financial risk and compliance specialist. Perform a comprehensive risk assessment of the financial analysis and investment recommendations for: {query}.
    
    Your job:
    1. Evaluate financial risks (credit, liquidity, market, operational)
    2. Assess industry-specific and regulatory risks
    3. Consider macroeconomic factors (inflation, rates, geopolitics)
    4. Run stress-test scenarios on investment recommendations
    5. Suggest risk mitigation and monitoring strategies
    6. Verify compliance with global financial regulations
    
    Provide objective risk ratings, quantitative measures where possible, and qualitative judgment for broader risks.
    """,
    expected_output="""
    A structured **Risk Assessment Report** containing:
    - Categorized risk list with severity ratings
    - Quantitative metrics (ratios, exposure levels) where available
    - Scenario analysis / stress test outcomes
    - Mitigation recommendations
    - Compliance checks and disclosures
    - Monitoring and governance requirements
    - Overall risk-adjusted investment perspective
    """,
    agent=risk_assessor,
    tools=[search, financial_document_tool],
    context=[analyze_financial_document, investment_analysis],
    async_execution=False,
)