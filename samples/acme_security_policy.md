# Acme Corp Information Security Policy
**Version:** 3.2
**Owner:** CISO Office
**Last reviewed:** March 2026

## 1. Purpose
This document defines the information security requirements for all employees, contractors, and third parties who access Acme systems or handle customer data.

## 2. Access Control
All access to production systems is controlled through our identity provider using SAML SSO. Multi-factor authentication (MFA) is required for all employees accessing systems classified as internal, confidential, or restricted. Role-based access control (RBAC) is enforced through our IAM platform, and all access is granted on a least-privilege basis.

Access reviews are conducted quarterly by each system owner, and accounts are deprovisioned within 24 hours of employee termination via an automated workflow in our HR system.

## 3. Encryption
All customer data at rest is encrypted using AES-256 via AWS KMS. Data in transit is protected using TLS 1.2 or higher. Customer-managed KMS keys are rotated annually and access to the keys is restricted to the platform security team.

## 4. Change Management
All production changes go through a formal change management process. Every change requires:
- A Jira ticket with business justification
- A pull request with code review by at least one senior engineer
- Automated CI/CD tests that must pass before deployment
- Approval from an authorized team lead

Rollback procedures are documented for every production deployment.

## 5. Security Monitoring
Acme operates a 24/7 Security Operations Center (SOC) staffed by our internal security team and supplemented by an external MDR provider. We use Splunk as our SIEM, CrowdStrike EDR on all endpoints, and Suricata IDS for network traffic. Alerts are triaged within 15 minutes and escalated to on-call engineers based on severity.

## 6. Incident Response
The Acme Incident Response Plan (IR-001) defines roles, responsibilities, and communication procedures for security incidents. Severity levels are defined as P0 (critical), P1 (high), P2 (medium), and P3 (low). The plan includes breach notification timelines that comply with GDPR (72 hours) and US state laws.

We conduct annual tabletop exercises to test the incident response plan and update it based on lessons learned.

## 7. Vendor Management
Third-party vendors that process customer data must complete a security review that includes:
- Review of their SOC 2 Type II report
- A signed Data Processing Agreement (DPA)
- Annual reassessment

We maintain a list of approved subprocessors on our website.

## 8. Backup and Recovery
Customer data is backed up daily to a geographically separate AWS region. Our disaster recovery plan targets a Recovery Time Objective (RTO) of 4 hours and a Recovery Point Objective (RPO) of 1 hour. We test failover twice per year.

## 9. Vulnerability Management
Vulnerability scans are run weekly using Qualys, and findings are triaged by the security team. Critical vulnerabilities must be remediated within 15 days, high within 30 days, medium within 90 days.

## 10. Training
All employees complete security awareness training within 30 days of joining Acme and annually thereafter. Training covers phishing, social engineering, password hygiene, and data handling. Completion is tracked in our LMS.

---
*Note: This policy intentionally does NOT cover a whistleblower or ethics hotline channel — this is tracked under HR policy HR-104 and is considered out of scope for information security.*
