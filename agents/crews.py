from crewai import Crew, Process, Task

from .agents import (
    market_research_agent,
    qa_market_research_agent,
    issue_triage_agent,
    qa_issue_triage_agent,
    doc_summarization_agent,
    qa_doc_summarization_agent,
    feature_prd_agent,
    qa_feature_prd_agent,
    release_notes_agent,
    qa_release_notes_agent,
    code_generation_agent,
    qa_code_generation_agent,
    code_review_agent,
    qa_code_review_agent,
    security_scan_agent,
    qa_security_scan_agent,
    deployment_agent,
    qa_deployment_agent,
    customer_support_agent,
    qa_customer_support_agent,
)


def make_crew(primary_agent, qa_agent, description):
    task1 = Task(description=description, agent=primary_agent, expected_output="A complete and accurate response.")
    task2 = Task(
        description="Review the response from the primary agent and provide feedback.",
        agent=qa_agent,
        expected_output="A review of the response, with suggestions for improvement.",
    )
    return Crew(
        agents=[primary_agent, qa_agent],
        tasks=[task1, task2],
        process=Process.sequential,
    )


market_research_crew = make_crew(
    market_research_agent, qa_market_research_agent, "Synthesize competitor data."
)
issue_triage_crew = make_crew(
    issue_triage_agent, qa_issue_triage_agent, "Triage a bug report."
)
doc_summarization_crew = make_crew(
    doc_summarization_agent,
    qa_doc_summarization_agent,
    "Summarize a long document.",
)
feature_prd_crew = make_crew(
    feature_prd_agent, qa_feature_prd_agent, "Write a PRD for a new feature."
)
release_notes_crew = make_crew(
    release_notes_agent, qa_release_notes_agent, "Write release notes."
)
code_generation_crew = make_crew(
    code_generation_agent, qa_code_generation_agent, "Write boilerplate code."
)
code_review_crew = make_crew(
    code_review_agent, qa_code_review_agent, "Review a pull request."
)
security_scan_crew = make_crew(
    security_scan_agent, qa_security_scan_agent, "Scan code for vulnerabilities."
)
deployment_crew = make_crew(
    deployment_agent, qa_deployment_agent, "Deploy the application."
)
customer_support_crew = make_crew(
    customer_support_agent,
    qa_customer_support_agent,
    "Respond to a customer support ticket.",
)
