# Security Policy

## Reporting a Vulnerability

If you discover a security issue, please do not open a public issue with exploit details.

Instead:

1. Contact the maintainer privately on GitHub.
2. Include steps to reproduce, impact, and suggested remediation.
3. Allow reasonable time for a fix before public disclosure.

## Scope

This policy applies to:

- Bot runtime code
- API authentication and authorization
- Secret handling and environment configuration
- Data handling in logs, DMs, and ticket transcripts

## Hardening Checklist

- Use strong random values for `API_SECRET` and `JWT_SECRET`
- Rotate API keys regularly
- Restrict admin/staff permissions in Discord
- Keep dependencies updated
