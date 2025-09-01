# Traceability Matrix

This document provides a traceability matrix for the ElectricEye Django project, mapping database tables to models, serializers, viewsets, and API URLs.

| DB Table      | Model   | Serializer        | ViewSet         | URL Example      |
|---------------|---------|-------------------|-----------------|------------------|
| `scans_scan`  | `Scan`  | `ScanSerializer`  | `ScanViewSet`   | `/api/scans/`    |
| `scans_finding`| `Finding`| `FindingSerializer`| `FindingViewSet`  | `/api/findings/` |
| `jobs_greetingjob` | `GreetingJob` | `GreetingJobSerializer` | `GreetingJobViewSet` | `/api/jobs/` | |
| `agents_agent` | `Agent` | `AgentSerializer` | `AgentViewSet` | `/api/agents/` |
| `agents_task` | `Task` | `TaskSerializer` | `TaskViewSet` | `/api/tasks/` |
| `agents_crew` | `Crew` | `CrewSerializer` | `CrewViewSet` | `/api/crews/` |
| `agents_job` | `Job` | `JobSerializer` | `JobViewSet` | `/api/agent-jobs/` |
| `billing_stripecustomer` | `StripeCustomer` | (N/A) | (N/A - Webhook) | `/api/billing/webhooks/` |
| `billing_subscription` | `Subscription` | (N/A) | (N/A) | (N/A) |
| `support_freshdeskticket`| `FreshdeskTicket`| `FreshdeskTicketSerializer` | `FreshdeskTicketView` | `/api/support/create-ticket/` |
