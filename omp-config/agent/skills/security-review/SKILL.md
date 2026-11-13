---
name: security-review
description: Review a diff or set of files for security issues in PHP and JavaScript web apps. Use before every commit that touches auth, input handling, queries, uploads, or ids.
---
First run `devstack-audit --diff HEAD` and include its summary. Treat its hits as leads and confirm them by reading the code.
Check and report each finding as: file:line, severity (critical, high, medium, low), issue, fix.
- SQL injection: any string-built query.
- XSS: unescaped output, innerHTML, html() with user data.
- CSRF missing on state-changing routes or Ajax calls.
- IDOR: records loaded by client id without an ownership or policy check.
- Exposed auto-increment ids anywhere client-visible.
- Mass assignment: $guarded = [] or request()->all() into create or update.
- Weak crypto: md5, sha1, mcrypt, ECB, custom crypto, hardcoded keys.
- Secrets in code, logs, or committed files.
- Unsafe uploads, open redirects, missing rate limits on auth.
- Comments, docblocks, em dashes, or en dashes added in violation of AGENTS.md.
End with a verdict: PASS or BLOCK, and the minimal fixes for BLOCK.
