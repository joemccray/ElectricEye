# Core Functionality of ElectricEye

This document outlines the core, non-redundant, and essential features of the ElectricEye security auditing tool.

## 1. Multi-Platform Security Auditing

ElectricEye's primary feature is its ability to perform security audits across a wide range of platforms. This is the core value proposition of the tool.

*   **Benefit:** Provides a single pane of glass for security posture management across a diverse set of cloud and SaaS environments.

### 1.1. Supported Platforms

*   **Cloud Service Providers (CSPs):**
    *   Amazon Web Services (AWS)
    *   Microsoft Azure
    *   Google Cloud Platform (GCP)
    *   Oracle Cloud Infrastructure (OCI)
    *   Alibaba Cloud
*   **Software-as-a-Service (SaaS) Providers:**
    *   ServiceNow
    *   Microsoft 365
    *   Salesforce
    *   Snowflake
    *   Google Workspace

## 2. Comprehensive Security Checks

ElectricEye includes a vast library of over 1000 security checks for the supported platforms. These checks cover a wide range of security domains.

*   **Benefit:** Enables deep and thorough security assessments of cloud and SaaS services, going beyond the surface-level checks.

### 2.1. Check Categories

*   Security Best Practices
*   Resilience and Recovery
*   Performance Optimization
*   Financial Best Practices
*   Identity and Access Management
*   Data Protection
*   Network Security

## 3. Compliance Framework Mapping

A key feature of ElectricEye is its mapping of security checks to over 20 industry and regulatory compliance frameworks.

*   **Benefit:** Helps organizations to assess their compliance posture against various standards and prepare for audits.

### 3.1. Supported Frameworks

*   NIST Cybersecurity Framework (CSF)
*   NIST SP 800-53
*   NIST SP 800-171
*   AICPA TSC (for SOC 2)
*   ISO/IEC 27001
*   CIS Critical Security Controls
*   PCI-DSS
*   HIPAA Security Rule
*   And many more...

## 4. Attack Surface Monitoring

ElectricEye integrates with external tools to provide attack surface monitoring capabilities.

*   **Benefit:** Helps organizations to identify and mitigate external-facing risks and vulnerabilities.

### 4.1. Integrated Tools

*   Shodan.io
*   VirusTotal
*   Nmap
*   detect-secrets
*   CISA Known Exploited Vulnerabilities (KEV) Catalog

## 5. Cloud Asset Management (CAM)

ElectricEye provides capabilities for discovering and managing cloud assets.

*   **Benefit:** Provides a centralized inventory of cloud assets, which is essential for security and governance.

## 6. Flexible Output and Reporting

ElectricEye supports a wide variety of output formats for its findings, allowing for easy integration with other tools and workflows.

*   **Benefit:** Enables seamless integration with existing security and DevOps toolchains.

### 6.1. Output Formats

*   **Human-Readable:**
    *   HTML Reports
    *   CSV
    *   Standard Output (stdout)
*   **Machine-Readable:**
    *   JSON
    *   Open Cyber Security Framework (OCSF)
*   **Security Tools:**
    *   AWS Security Hub
    *   FireMon Cloud Defense
*   **Databases:**
    *   Amazon DocumentDB
    *   MongoDB
    *   PostgreSQL
*   **Messaging and Queuing:**
    *   Slack
    *   Amazon SQS

## 7. Configuration and Extensibility

ElectricEye is highly configurable and extensible, allowing users to tailor it to their specific needs.

*   **Benefit:** Provides flexibility and allows the tool to adapt to different environments and requirements.

### 7.1. Key Features

*   **TOML-based Configuration:** For managing credentials, targets, and other settings.
*   **Plugin-based Architecture:** Allows for the easy addition of new auditors and checks.
*   **Powerful CLI:** Provides granular control over the auditing process.
*   **Docker Support:** Simplifies deployment and ensures a consistent environment.
