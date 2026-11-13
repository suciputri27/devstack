---
name: security-audit
description: Attack-style security audit of the current app with fan-out subagents, adversarial verification, and a report with fixes and regression tests. Use when the operator asks for a security audit, pentest, "cek keamanan", before a release, or after large changes.
---

# Security audit

Goal: find real, exploitable problems, prove each one, and hand back fixes with tests. A short report of confirmed issues beats a long list of guesses.

## 0. Safety (RULES)
- Targets: the local codebase and dev or staging URLs only. Never production, never a URL the operator did not give in chat.
- No destructive requests (no deletes, no mass writes, no load testing). Use test accounts only. Never read or print real personal data or secrets; mask them in the report.
- Do not fix anything before the report is shown, unless the operator's request explicitly said to fix.

## 1. Phase 1: deterministic scan (no model cost)
```bash
devstack-audit                                  # full, codebase
devstack-audit --diff origin/main               # quick, changed files only
devstack-audit --url http://localhost:8001      # add header and exposure checks
```
Read `.ai/security/phase1.md`, not the JSON, unless you need a specific record.

## 2. Choose the mode
- QUICK (diff with 10 files or fewer, or a PR): one `security-auditor` subagent, all area checklists, only the changed files plus files they call.
- FULL (before a release, weekly, or when asked): one `security-auditor` subagent per area, in parallel:
  `authz-idor`, `injection`, `auth-session`, `upload-ssrf`, `business-logic`, `config-secrets`.

## 3. Brief each auditor (keep it small)
Give each subagent only:
- its checklist path: `/opt/devstack/audit/areas/<area>.md`
- the phase 1 findings for its area (copy the lines from phase1.md)
- the relevant routes from `phase1.json` and at most 15 relevant files (find them with grep on route names, controllers, models, middleware, policies)
- the stack line from AGENTS.md (framework, version, mode)
- the output schema below
Ask for at most 8 findings, most severe first, and a summary under 1,500 tokens.

Finding schema:
```json
{"id": "AUTHZ-1", "area": "authz-idor", "title": "", "severity": "critical|high|medium|low",
 "location": "path:line", "evidence": "code excerpt or request and response",
 "attack": "steps an attacker takes", "preconditions": "", "impact": "", "confidence": "high|medium|low",
 "fix": "concrete change", "test": "regression test idea"}
```
No evidence, no finding. A phase 1 hit is a lead, not a finding, until the code path is read.

## 4. Verify (adversarial)
Send all findings to one `security-verifier` subagent. It tries to disprove each one: middleware, policies, global scopes, validation, framework defaults, route constraints. With a dev URL it may reproduce using a safe, read-only request and a test account. Verdicts: `confirmed`, `false_positive`, `needs_human`, each with a one-line reason.

## 5. Severity rubric
- critical: unauthenticated access to other users' data, remote code execution, auth bypass, SQL injection with data access.
- high: authenticated IDOR, stored XSS, privilege escalation, secret leak, payment or quota tampering.
- medium: reflected XSS, CSRF on state change, missing rate limit on auth, weak upload validation, verbose errors.
- low: missing headers, version leaks, hardening gaps.

## 6. Report `.ai/security/report.md`
1. Summary table: id, severity, title, status (open, fixed, accepted).
2. Each confirmed finding: location, evidence (secrets masked), attack, impact, fix as a patch, regression test code, effort.
3. Phase 1 items not covered above (dependencies, headers, exposures).
4. Infrastructure recommendations (WAF or CDN, rate limits at Nginx, backups).
5. False positives in one line each, so they are not re-reported.
Tell the operator the counts per severity and where the report is.

## 7. Fixing (after approval)
- One finding per commit: the fix plus its regression test that fails before and passes after.
- Re-run phase 1 and the project tests. Update the status column in the report.
- Never weaken a rule in BACKEND.md to make a finding disappear.
