# Security Policy

## Supported versions
Security updates are provided for the latest version on the default branch (`main`). Older tags/releases may not receive security patches.

## Reporting a vulnerability
Please do not report security vulnerabilities through public GitHub issues.

Preferred reporting methods:
1. GitHub Security Advisories (if enabled): "Report a vulnerability"
2. Private contact to the maintainers (e.g., email)

If you need a contact channel and none is listed, open an issue requesting a private contact method and do not include sensitive details.

When reporting, include:
- A clear description of the vulnerability and impact
- Steps to reproduce (or a proof-of-concept)
- Affected components (bot/api/worker, endpoints, versions/commit)
- Any relevant logs with secrets removed

## Our response process
- We will acknowledge receipt as soon as practical.
- We will investigate and may request additional information.
- We will work on a fix and coordinate a release/deploy.

## Disclosure
We follow responsible disclosure. Please allow time to validate and patch the issue before public disclosure.

## Security best practices (for contributors)
- Never commit secrets (tokens, API keys, `.env` files).
- Use GitHub Secrets for CI/CD.
- Rotate credentials immediately if exposure is suspected.
- Prefer least-privilege credentials for production deployments.
