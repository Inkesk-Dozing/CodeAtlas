# Security Policy

## Supported Versions

The following table lists the supported versions of CodeAtlas for security patches.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

## Reporting a Vulnerability

The CodeAtlas project team takes security seriously. If you discover a security vulnerability within CodeAtlas, please follow these guidelines to report it privately:

### Contact Protocol

- **Do NOT** open a public GitHub issue for security vulnerabilities.
- Submit reports directly via GitHub Private Vulnerability Reporting or email the security response team at `security@codeatlas.dev`.
- Include detailed steps to reproduce, potential impact analysis, and proof-of-concept payloads where applicable.

### Response Timelines

- **Acknowledgement**: Within 24 hours of report receipt.
- **Initial Assessment & CVSS Scoring**: Within 48 hours.
- **Remediation & Patch Release**: Within 7 business days for Critical/High severity vulnerabilities, 30 days for Medium/Low.

### Disclosure Policy

We practice Coordinated Vulnerability Disclosure (CVD). We ask reporters to allow us a reasonable time frame to remediate the issue prior to public release.

## Security Scanning & CI/CD Pipeline Controls

CodeAtlas implements continuous automated security scanning:

1. **Dependency Vulnerability Scanning**: Automated Snyk and Dependabot checks blocking critical/high CVE merges.
2. **Static Application Security Testing (SAST)**: CodeQL scans executed on every pull request targeting `main`.
3. **Secret Detection**: TruffleHog pre-commit hooks and GitHub Secret Scanning protecting against hardcoded credentials, JWT keys, and API tokens.
4. **Container Image Scanning**: Trivy vulnerability scanning for `apps/api` and `apps/web` Docker build artifacts.
