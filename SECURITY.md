# Security Policy

## Supported Versions

The latest minor release on the `master` branch receives security fixes.

## Reporting a Vulnerability

**Please do not open a public issue for security reports.**

Use GitHub's private vulnerability reporting:
[Report a vulnerability](https://github.com/qsale-io/qsale-mcp-server/security/advisories/new).

Include:

- A description of the vulnerability.
- Steps to reproduce.
- The version (commit SHA) of `qsale-mcp` you tested against.
- Any suggested mitigation, if you have one.

You will receive an acknowledgement within 3 business days. We will keep you
updated as the fix is investigated, prepared, and released.

## Scope

In-scope:

- Code in this repository.
- Default configuration shipped in the repository.

Out of scope:

- Third-party tokens leaked by misconfigured deployments.
- Vulnerabilities in upstream dependencies — please report those upstream
  first; let us know via an advisory once a fix is available so we can
  bump the pin.
- The QSale REST API itself — report those to the QSale platform team.

## Disclosure Policy

We follow coordinated disclosure: once a fix is available we publish a
release note and credit the reporter unless anonymity is requested.
