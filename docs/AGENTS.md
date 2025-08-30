# AGENTS

## Dev Agent
- Implement features per PRD and ADRs. Respect typed schemas and tests-first.
- Use **information-dense** prompts with explicit file paths (ADD/UPDATE/DELETE/ADD TEST).

## QA Agent
- Write integration tests that hit real code paths.
- Enforce coverage threshold and fail until green.

## Docs Agent
- Keep PRD/ADRs/task specs current. Append ADRs after significant changes.

## Infra Agent
- Ensure CI passes: lint, types, tests, ADR check.
