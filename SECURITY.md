# Security Policy

## Scope

This document applies to the NetReaper source code hosted in this repository.
It does not apply to security issues resulting from misuse of the tool.

## Supported Versions

| Version | Status |
|---|---|
| 1.0.x | Supported |

## Reporting a Vulnerability

If you discover a security vulnerability in NetReaper itself (such as an
argument injection flaw, path traversal in report handling, or privilege
escalation in the installer), do not open a public issue.

Report the vulnerability privately by opening a GitHub Security Advisory
on this repository:

Settings -> Security -> Advisories -> New draft security advisory

Include in your report:
- A description of the vulnerability and its potential impact
- The file and line number where the issue exists
- A minimal reproduction case
- Your suggested fix if you have one

You will receive a response within 72 hours. Critical vulnerabilities will
be patched and a new release published within 14 days of confirmation.

## Out of Scope

Vulnerabilities in third-party tools that NetReaper invokes (nmap, john,
aircrack-ng, etc.) should be reported to those projects directly.

Legal consequences of using NetReaper against unauthorized targets are
entirely the responsibility of the operator and are out of scope for
this security policy.
