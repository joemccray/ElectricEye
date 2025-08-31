# Jules Django Development & Testing Prompts

This file contains the mandatory prompts to ensure the Django application is developed, tested, and configured according to project standards.

---

## Prompt 0: Initial Setup
**Context:** This prompt ensures that the development environment is correctly configured before any development or testing tasks begin. This is the foundational step for all subsequent prompts.

**Task:**
Execute the Django project setup script to configure the environment.

```bash
python jules-django-setup.py
```

**Post-Execution Mandates**  
- **Traceability Matrix:** Build the initial traceability matrix with headers: `DB Table | Model | Serializer | ViewSet | URL Example | Tasks`.
- **Model Verification:** Verify that all models appear in the matrix and are reachable via REST APIs.
- **Test Suite Prerequisite:** Verify that all tasks outlined in `jules-backend-testsuite-prompts.md` have been successfully executed.
- **Quality Checks:** Verify there are zero errors from `python manage.py check`, `pytest`, `flake8`, and `bandit`.
- **Logging:** Log the commands executed and any errors fixed with a detailed breakdown in `logs/jules-dev.log`.
- **Reflection:** Reflect on your work and provide proof that you have completed each task as described.

---

## Prompt 1: Application Logic Analysis & Enhancement
**Context:** Evaluate and optimize the core business logic of the application to ensure it efficiently and effectively serves the target users (ICPs).

**Tasks:**
1. **Analyze** the application logic for both effectiveness and efficiency on a scale of 1 to 10 (1=worst, 10=best), specifically for your ICPs.  
   References:  
   - <http://146.190.150.94/app-reference-docs/Django-Business-Logic.md>  
   - <http://146.190.150.94/app-reference-docs/Django-clerk.md>
2. **Enhance** the application logic to ensure that all analyzed items score no less than a 9.5. The code must be production-ready, fully tested (unit and integration), self-documenting, and adhere to PEP 8 with zero linting errors. Ensure the code is 100% functional, with no example code or TODOs.

**Post-Execution Mandates**  
- **Traceability Matrix:** Update the traceability matrix to reflect all changes.
- **Model Verification:** Verify that all models appear in the matrix and are reachable via REST APIs.
- **Test Suite Prerequisite:** Verify that all tasks outlined in `jules-backend-testsuite-prompts.md` have been successfully executed.
- **Quality Checks:** Verify there are zero errors from `python manage.py check`, `pytest`, `flake8`, and `bandit`.
- **Logging:** Log the commands executed and any errors fixed with a detailed breakdown in `logs/jules-dev.log`.
- **Reflection:** Reflect on your work and provide proof that you have completed each task as described.

---

## Prompt 2: Data Flow Analysis & Enhancement
**Context:** Examine and improve how data moves through the application to ensure optimal performance and integrity for your target users.

**Tasks:**
1. **Analyze** the application data flow for both effectiveness and efficiency on a scale of 1 to 10 (1=worst, 10=best), specifically for your ICPs.  
   Reference: <http://146.190.150.94/app-reference-docs/Django-Data-Flow.md>.
2. **Enhance** the data flow to ensure that all analyzed items score no less than a 9.5. The code must be production-ready, fully tested (unit and integration), self-documenting, and adhere to PEP 8 with zero linting errors. Ensure the code is 100% functional, with no example code or TODOs.

**Post-Execution Mandates**  
- **Traceability Matrix:** Update the traceability matrix to reflect all changes.
- **Model Verification:** Verify that all models appear in the matrix and are reachable via REST APIs.
- **Test Suite Prerequisite:** Verify that all tasks outlined in `jules-backend-testsuite-prompts.md` have been successfully executed.
- **Quality Checks:** Verify there are zero errors from `python manage.py check`, `pytest`, `flake8`, and `bandit`.
- **Logging:** Log the commands executed and any errors fixed with a detailed breakdown in `logs/jules-dev.log`.
- **Reflection:** Reflect on your work and provide proof that you have completed each task as described.

---

## Prompt 3: DRF Analysis & Enhancement
**Context:** Evaluate and optimize the application's API implementation to ensure it effectively and efficiently serves your target users.

**Tasks:**
1. **Analyze** the Django REST Framework (DRF) implementation for its readiness to serve your specific ICPs, rating both effectiveness and efficiency on a scale of 1 to 10 (1=worst, 10=best).  
   Reference: <http://146.190.150.94/app-reference-docs/Django-REST-Framework-Cheat-Sheet.md>.
2. **Enhance** the DRF implementation to ensure that all analyzed items score no less than a 9.5. The code must be production-ready, fully tested (unit and integration), self-documenting, and adhere to PEP 8 with zero linting errors. Ensure the code is 100% functional, with no example code or TODOs.

**Post-Execution Mandates**  
- **Traceability Matrix:** Update the traceability matrix to reflect all changes.
- **Model Verification:** Verify that all models appear in the matrix and are reachable via REST APIs.
- **Test Suite Prerequisite:** Verify that all tasks outlined in `jules-backend-testsuite-prompts.md` have been successfully executed.
- **Quality Checks:** Verify there are zero errors from `python manage.py check`, `pytest`, `flake8`, and `bandit`.
- **Logging:** Log the commands executed and any errors fixed with a detailed breakdown in `logs/jules-dev.log`.
- **Reflection:** Reflect on your work and provide proof that you have completed each task as described.

---

## Prompt 4: AI Agent Implementation
**Context:** Enhance the application with a production-grade CrewAI-based agent system, operable via DRF APIs, to deliver measurable value to ICPs.

**Tasks:**
- **Create CrewAI Agents:** Implement at least 10 primary CrewAI agents and 10 corresponding QA agents. Each agent must be a specialist with a clear Role, Goal, and Backstory. QA agents must be configured to validate the primary agent's output against acceptance criteria.
- **Implement CrewAI Workflows:** Integrate the agents into at least 10 collaborative workflows (crews). Each workflow must have a minimum of 3 steps (an agent/QA pair execution) and be designed to reduce the ICPs' average time on task by at least 50%.
  - Reference: <http://146.190.150.94/app-reference-docs/Django-CrewAI.v2.md>.
- Ensure all code is 100% functional, production-ready, and contains no example code or TODOs.

**Post-Execution Mandates**  
- **Traceability Matrix:** Update the traceability matrix to reflect all new models, serializers, and views for the agent system.
- **Model Verification:** Verify that all models appear in the matrix and are reachable via REST APIs.
- **Test Suite Prerequisite:** Verify that all tasks outlined in `jules-backend-testsuite-prompts.md` have been successfully executed.
- **Quality Checks:** Verify there are zero errors from `python manage.py check`, `pytest`, `flake8`, and `bandit`.
- **Logging:** Log the commands executed and any errors fixed with a detailed breakdown in `logs/jules-dev.log`.
- **Reflection:** Reflect on your work and provide proof that you have completed each task as described.

---

## Prompt 5: SaaS Readiness Implementation
**Context:** Prepare the application for commercial launch as a multi-tenant SaaS solution with robust billing, authentication, and support features.

**Tasks:**
- **Analyze SaaS Readiness:** Analyze the application's readiness to serve ICPs as a SaaS solution, rating effectiveness and efficiency on a scale of 1 to 10 (1=worst, 10=best).  
  References:  
  - <http://146.190.150.94/app-reference-docs/Django-SaaS.md>  
  - <http://146.190.150.94/app-reference-docs/Django-clerk.md>
- **Implement Stripe Billing:** Integrate Stripe subscription billing with Clerk for the following tiers: Free, $9/month, $19/month, and $39/month.
- **Configure Clerk Authentication:** Ensure both the backend and frontend are configured to use Clerk for authentication, including token refresh handling.  
  Reference: <http://146.190.150.94/app-reference-docs/Clerk+Token+Refresh+Issue+v2.pdf>.
- **Integrate Freshdesk:** Natively allow users to create Freshdesk trouble tickets from within the application.  
  Reference: <http://146.190.150.94/app-reference-docs/Django-Freshdesk.md>.
- **Final Enhancements:** Perform all enhancements required to ensure all items from the analysis and implementation tasks score no less than a 9.5. The code must be production-ready, fully tested, self-documenting, and adhere to PEP 8 with zero linting errors. Ensure the code is 100% functional, with no example code or TODOs.

**Post-Execution Mandates**  
- **Traceability Matrix:** Update the traceability matrix to reflect all changes.
- **Model Verification:** Verify that all models appear in the matrix and are reachable via REST APIs.
- **Test Suite Prerequisite:** Verify that all tasks outlined in `jules-backend-testsuite-prompts.md` have been successfully executed.
- **Quality Checks:** Verify there are zero errors from `python manage.py check`, `pytest`, `flake8`, and `bandit`.
- **Logging:** Log the commands executed and any errors fixed with a detailed breakdown in `logs/jules-dev.log`.
- **Reflection:** Reflect on your work and provide proof that you have completed each task as described.

---

## Prompt 6: Railway Deployment & API Specification
**Context:** Configure the Django project for seamless deployment on Railway and provide a comprehensive API specification.

**Tasks:**
- **Configure for Railway:** Ensure the application is configured for native deployment on Railway.  
  Reference: <http://146.190.150.94/app-reference-docs/Railway-Native-Django-Deployment-Tips.md>.
- **Create OpenAPI Specification:** Generate a complete YAML OpenAPI specification file named `[product-name]-api-spec.yaml`.

**Post-Execution Mandates**  
- **Traceability Matrix:** Update the traceability matrix to reflect any deployment-specific changes.
- **Model Verification:** Verify that all models appear in the matrix and are reachable via REST APIs.
- **Test Suite Prerequisite:** Verify that all tasks outlined in `jules-backend-testsuite-prompts.md` have been successfully executed.
- **Quality Checks:** Verify there are zero errors from `python manage.py check`, `pytest`, `flake8`, and `bandit`.
- **Logging:** Log the commands executed and any errors fixed with a detailed breakdown in `logs/jules-dev.log`.
- **Reflection:** Reflect on your work and provide proof that you have completed each task as described.

---

## Prompt 7: Source Code Review & Refinement
**Context:** Conduct a detailed quality assurance review of the codebase and implement necessary improvements to meet coding standards.

**Tasks:**
- **Analyze Codebase:** Perform a detailed analysis of the application against every check in the <http://146.190.150.94/app-reference-docs/Code-Review-Template.md> document, covering all categories (Module Header, Declarations, Function Headers, Lint Results, Code Checks).
- **Enhance Codebase:** Refactor and enhance the application to satisfy every check from the code review template, ensuring full compliance.

**Post-Execution Mandates**  
- **Traceability Matrix:** Update the traceability matrix to reflect any refactoring.
- **Model Verification:** Verify that all models appear in the matrix and are reachable via REST APIs.
- **Test Suite Prerequisite:** Verify that all tasks outlined in `jules-backend-testsuite-prompts.md` have been successfully executed.
- **Quality Checks:** Verify there are zero errors from `python manage.py check`, `pytest`, `flake8`, and `bandit`.
- **Logging:** Log the commands executed and any errors fixed with a detailed breakdown in `logs/jules-dev.log`.
- **Reflection:** Reflect on your work and provide proof that you have completed each task as described.
