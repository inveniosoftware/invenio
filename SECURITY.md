# Security Policy

## Supported Versions

| Version   | Supported          |
| --------- | ------------------ |
| 3.5.x     | :white_check_mark: |
| 3.4.x     | :white_check_mark: |
| < 3.4     | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests.**

Instead, report them privately via email to
**[info@inveniosoftware.org](mailto:info@inveniosoftware.org)**.

Please include as much of the following information as possible to help us
triage your report:

- Type of issue (e.g. authentication bypass, SQL injection, cross-site
  scripting, remote code execution)
- Full paths of source file(s) related to the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## Response Process

1. **Acknowledgement**: We will acknowledge receipt of your report within
   **3 business days**.

2. **Assessment**: A member of the core security team will assess the severity
   and impact of the issue. We classify vulnerabilities as:
   - **High severity** -- impacts running installations in a way that allows
     unprivileged access to data, destruction of data, leaking user
     information, or rendering a system unusable. Examples: authentication
     bypass, remote code execution, XSS, SQL injection.
   - **Low severity** -- does not affect installations directly, requires
     pre-existing access or misconfiguration. Examples: weak file permissions
     in Docker images, theoretical cryptographic weaknesses.

3. **Fix development**: We will develop a fix privately and prepare patches
   for all supported versions.

4. **Disclosure**: We will coordinate disclosure with the reporter. Fixes are
   released simultaneously with an advisory. We aim to release a fix within
   **14 days** of confirming a high-severity issue.

## Disclosure Policy

- High-severity issues are handled privately by a small group of core
  maintainers until a fix is released.
- Security advisories are published through
  [GitHub Security Advisories](https://github.com/inveniosoftware/invenio/security/advisories)
  and announced on the project mailing list.
- We follow coordinated disclosure: the reporter is credited (unless they
  prefer anonymity) and the advisory is published when the fix is available.

## Preferred Languages

We accept vulnerability reports in **English**.
