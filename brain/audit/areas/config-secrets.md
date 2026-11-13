# Area: configuration, secrets, and exposure

Question: does the deployment leak secrets, debug information, or internal files?
- Secrets: none in code, configs, JS bundles, or git history (`git log -p -S 'password'` on suspicious files). `.env` not tracked. Keys rotated if ever committed.
- Debug: `APP_DEBUG=false` and `ENVIRONMENT=production` in production configs; error pages generic; no `phpinfo`, Telescope, Debugbar, or Horizon dashboards exposed without auth.
- Web server: document root is `public/` (Laravel) or a dedicated folder; `.env`, `.git`, `storage`, `vendor`, `application/logs` not reachable.
- Headers: CSP, HSTS, nosniff, frame-ancestors, Referrer-Policy; cookies flags.
- CORS: explicit origins; no `*` with credentials.
- Dependencies: `composer audit`, `npm audit` results from phase 1; abandoned packages.
- Logging: no passwords, tokens, or personal data in logs; log files not public.
- Backups and exports: not stored in public paths, not guessable names.
Evidence: config file lines, phase 1 exposure results, or a read-only request.
