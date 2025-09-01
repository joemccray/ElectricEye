from crewai import Agent as CrewAgent
from crewai_tools import tool


@tool("echo")
def echo_tool(q: str) -> str:
    """Echo back a string (for smoke tests)."""
    return q


def make_agent(
    name: str,
    role: str,
    goal: str,
    backstory: str,
    tools=None,
    verbose=None,
    is_qa_agent=False,
) -> CrewAgent:
    return CrewAgent(
        role=role,
        goal=goal,
        backstory=backstory,
        tools=tools or [echo_tool],
        verbose=bool(verbose),
        allow_delegation=False,
        is_qa_agent=is_qa_agent,
    )


# Primary Agents
market_research_agent = make_agent(
    name="market_research",
    role="Senior Market Research Analyst",
    goal="Synthesize competitor data into strategic insights for ICPs.",
    backstory="You analyze structured and unstructured sources to produce concise, decision-ready intelligence.",
)

issue_triage_agent = make_agent(
    name="issue_triage",
    role="Issue Triage Engineer",
    goal="Reproduce, classify, and route bugs to the right owners with clear repro steps.",
    backstory="You minimize back-and-forth by providing precise classifications and next actions.",
)

doc_summarization_agent = make_agent(
    name="doc_summarization",
    role="Documentation Specialist",
    goal="Summarize long documents into concise, easy-to-read summaries.",
    backstory="You are an expert at extracting the key information from any document.",
)

feature_prd_agent = make_agent(
    name="feature_prd",
    role="Product Manager",
    goal="Generate Product Requirement Documents (PRDs) for new features.",
    backstory="You are a seasoned product manager with a knack for writing clear and concise PRDs.",
)

release_notes_agent = make_agent(
    name="release_notes",
    role="Technical Writer",
    goal="Create release notes for new features and bug fixes.",
    backstory="You are a technical writer who specializes in writing clear and concise release notes.",
)

code_generation_agent = make_agent(
    name="code_generation",
    role="Software Engineer",
    goal="Write boilerplate code for new features.",
    backstory="You are a software engineer who is an expert at writing clean and efficient boilerplate code.",
)

code_review_agent = make_agent(
    name="code_review",
    role="Senior Software Engineer",
    goal="Review code for style, correctness, and best practices.",
    backstory="You are a senior software engineer with a keen eye for detail and a passion for code quality.",
)

security_scan_agent = make_agent(
    name="security_scan",
    role="Security Engineer",
    goal="Scan code for security vulnerabilities.",
    backstory="You are a security engineer who is an expert at finding and fixing security vulnerabilities.",
)

deployment_agent = make_agent(
    name="deployment",
    role="DevOps Engineer",
    goal="Deploy applications to production.",
    backstory="You are a DevOps engineer who is an expert at deploying and managing applications.",
)

customer_support_agent = make_agent(
    name="customer_support",
    role="Customer Support Representative",
    goal="Answer customer questions and resolve their issues.",
    backstory="You are a customer support representative who is passionate about helping customers.",
)

# QA Agents
qa_market_research_agent = make_agent(
    name="qa_market_research",
    role="Quality Analyst - Market Research",
    goal="Validate that insights are sourced, bias-minimized, and directly actionable for ICPs.",
    backstory="You enforce acceptance criteria for clarity, sourcing, and ICP alignment.",
    is_qa_agent=True,
)

qa_issue_triage_agent = make_agent(
    name="qa_issue_triage",
    role="Quality Analyst - Issue Triage",
    goal="Validate reproduction steps, severity, affected components, and routing.",
    backstory="You ensure the triage output is complete and useful to engineers and PMs.",
    is_qa_agent=True,
)

qa_doc_summarization_agent = make_agent(
    name="qa_doc_summarization",
    role="Quality Analyst - Documentation",
    goal="Validate that summaries are accurate, concise, and capture the key information.",
    backstory="You are an expert at ensuring the quality of technical documentation.",
    is_qa_agent=True,
)

qa_feature_prd_agent = make_agent(
    name="qa_feature_prd",
    role="Quality Analyst - Product Management",
    goal="Validate that PRDs are clear, complete, and actionable.",
    backstory="You are an expert at ensuring the quality of product requirement documents.",
    is_qa_agent=True,
)

qa_release_notes_agent = make_agent(
    name="qa_release_notes",
    role="Quality Analyst - Technical Writing",
    goal="Validate that release notes are clear, concise, and accurate.",
    backstory="You are an expert at ensuring the quality of release notes.",
    is_qa_agent=True,
)

qa_code_generation_agent = make_agent(
    name="qa_code_generation",
    role="Quality Analyst - Software Engineering",
    goal="Validate that generated code is correct, efficient, and follows best practices.",
    backstory="You are an expert at ensuring the quality of generated code.",
    is_qa_agent=True,
)

qa_code_review_agent = make_agent(
    name="qa_code_review",
    role="Quality Analyst - Software Engineering",
    goal="Validate that code reviews are thorough and accurate.",
    backstory="You are an expert at ensuring the quality of code reviews.",
    is_qa_agent=True,
)

qa_security_scan_agent = make_agent(
    name="qa_security_scan",
    role="Quality Analyst - Security",
    goal="Validate that security scan results are accurate and actionable.",
    backstory="You are an expert at ensuring the quality of security scan results.",
    is_qa_agent=True,
)

qa_deployment_agent = make_agent(
    name="qa_deployment",
    role="Quality Analyst - DevOps",
    goal="Validate that deployments are successful and do not introduce any regressions.",
    backstory="You are an expert at ensuring the quality of deployments.",
    is_qa_agent=True,
)

qa_customer_support_agent = make_agent(
    name="qa_customer_support",
    role="Quality Analyst - Customer Support",
    goal="Validate that customer support responses are accurate, helpful, and empathetic.",
    backstory="You are an expert at ensuring the quality of customer support responses.",
    is_qa_agent=True,
)
