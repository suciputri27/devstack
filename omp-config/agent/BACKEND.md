# Backend brain

Read this once per backend task (endpoints, queries, jobs, schema, integrations). Three levels:
- RULES: always, even when the request does not mention them. A short request ("buat fitur daftar pesanan") still gets every rule.
- DEFAULTS: use unless the project already does it differently (MIRROR) or the operator chose otherwise.
- CHOICES: the operator decides (transport, cache, search engine, auth style). Support whatever they pick and apply its safety rules from section 9.

## 1. Before coding
- Detect the mode: existing codebase = MIRROR (copy its structure, naming, query style, response format); new project = STANDARD (clean architecture, section 2). Security and performance RULES apply in both modes; if the existing style breaks one, follow the rule and report it.
- Read up to 3 files near the change and the related migrations. Know the table sizes you are touching (`SELECT reltuples FROM pg_class WHERE relname = '...'` or `SHOW TABLE STATUS`), or ask.
- For every new query, decide: who may call it, how many rows it can return, which index serves it.

## 2. Architecture (STANDARD)
- Domain (entities, value objects, repository interfaces), Application (use cases, services, DTOs), Infrastructure (Eloquent or query builder repositories, external clients, cache, queue), Presentation (controllers, FormRequests, resources, views).
- Controllers: validate, authorize, call one use case, return a resource. No queries, no business rules.
- One use case per action (`CreateOrder`, `CancelOrder`), injected dependencies, no static facades inside Domain or Application.
- PHP: `declare(strict_types=1)`, typed everything, final classes, readonly DTOs, enums for states.

## 3. Data and performance (RULES)
- No N+1: eager load relations, or join. In Laravel enable `Model::preventLazyLoading(! app()->isProduction())`.
- Select only needed columns. No `SELECT *` in list or API queries.
- Every list is paginated. Never return an unbounded collection. Max page size 100.
- Pagination type:
  - Infinite scroll, feeds, timelines, large or fast-growing tables, exports: keyset (cursor) pagination on an indexed, unique ordering (`created_at, id` or UUIDv7). Laravel `cursorPaginate()`; CI3 `WHERE (created_at, id) < (?, ?) ORDER BY created_at DESC, id DESC LIMIT ?`.
  - Small admin tables where users jump to page N: offset pagination is fine.
- Every column in WHERE, JOIN, ORDER BY of a frequent query is indexed; composite index order follows the query (equality columns first, then range or sort).
- No queries inside loops. Batch with `whereIn`, upserts, or chunked inserts.
- Large processing: `chunkById` or `lazyById` (Laravel), keyset loops (CI3). Never load a whole table into memory.
- Avoid `COUNT(*)` on large tables per request: cache it, use estimates, or show "lebih dari 10.000".
- Leading-wildcard `LIKE '%x%'` on large tables is not search; see section 5.
- Multi-step writes run in a transaction. Lock rows (`lockForUpdate`) when two requests can race (stock, quota, queue numbers).
- New heavy query on a table over ~100k rows: run `EXPLAIN` and include the plan summary in the report.
- Money: integer minor units or DECIMAL, never float. Time: store UTC, display Asia/Jakarta.

## 4. Identifiers (RULES)
- Never expose auto-increment IDs: URLs, route params, API responses, HTML attributes, JS, error messages.
- New tables: UUIDv7 primary key. Legacy integer tables: add a unique `public_id` UUID and use it on every external surface; resolve to the internal id server-side.
- Validate UUID format before lookup. Lookups always include ownership or tenant scope (`where('user_id', $user->id)`), never the id alone.
- If an operator explicitly wants encrypted ids instead of UUIDs, use authenticated encryption (libsodium) with a key from `.env`. Never Hashids or base64 as "encryption".

## 5. Search (when a search feature is asked)
Pick by data size and need, then tell the operator which tier you used:
| tier | when | how |
| --- | --- | --- |
| prefix | under ~50k rows, names or codes | indexed normalized column (`lower`, trimmed), `LIKE 'term%'` |
| full text | up to millions of rows, words in text | PostgreSQL `tsvector` + GIN with `simple` config and `unaccent`; MySQL `FULLTEXT` in boolean mode |
| fuzzy | typos, partial words | PostgreSQL `pg_trgm` GIN index with `similarity` or `%` |
| engine | facets, ranking, instant search at scale | Meilisearch or Typesense (a CHOICE), synced by queued jobs |
- Always: minimum 2 characters, server-side limit, keyset pagination, results ranked, the matched field returned for highlighting.
- Client: debounce 250 to 300ms, cancel the previous request (AbortController), show skeleton while loading and an empty state with a suggestion.
- Encrypted fields are searchable only by exact match through a blind index (HMAC-SHA256 with a separate key).

## 6. Security (RULES)
- Validate every input server-side with an allowlist (FormRequest or a dedicated validator). Client validation is UX only.
- Authorize every endpoint (Policies or Gates; CI3 explicit ownership checks). Write a test where another user gets 403 or 404.
- SQL only with bindings. Output escaped (Blade `{{ }}`, `html_escape()`, `textContent`). CSRF on every state change, Ajax included.
- Mass assignment: explicit `$fillable`. Never `$guarded = []`.
- Passwords Argon2id. Sensitive columns encrypted at rest (AES-256-GCM casts or libsodium). Keys only in `.env`.
- Uploads: validate MIME by content and size, random names, store outside the public root, serve through authorized routes or short signed URLs.
- No server-side fetch of user-supplied URLs without an allowlist (SSRF). No `unserialize`, `eval`, or shell calls with user input.
- Security headers on every response: CSP (no `unsafe-inline` for new code), HSTS, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `frame-ancestors 'none'` unless embedding is required.
- CORS: explicit origins only, never `*` with credentials.
- Sessions: HttpOnly, Secure, SameSite=Lax, regenerate on login, idle timeout for admin areas.
- Errors: generic messages to clients, details only in logs. Never log passwords, tokens, keys, or personal data.
- Audit trail (who, what, when, from where) for sensitive actions: role changes, deletes, exports, payments, login failures.
- `composer audit` and `npm audit` clean or explained before finishing.

## 7. Abuse and DDoS (RULES, application level)
The application cannot stop a volumetric DDoS; it must not amplify one and must survive abuse:
- Rate limit by user and IP: login and OTP 5 per minute, password reset 3 per hour, search 30 per minute, general API 60 per minute, exports 5 per hour. Return 429 with `Retry-After`.
- Lock or slow down accounts after repeated failed logins; notify the user.
- Cap request body size, page size, upload size, and query complexity. Set timeouts on DB queries and outbound HTTP (connect 3s, total 10s).
- Move slow work to queues: email, PDF, exports, imports, image processing, webhooks.
- Cache hot public reads with short TTLs. Public forms get a challenge (Cloudflare Turnstile or similar) after a threshold.
- Report infrastructure recommendations instead of claiming the app is DDoS-proof: CDN or WAF in front, Nginx `limit_req`, fail2ban.

## 8. Reliability (DEFAULTS)
- Idempotency for anything that must not happen twice (payments, submissions, queue numbers): idempotency key or unique constraint plus a clear duplicate response.
- External calls: timeout, retry with backoff on 5xx and timeouts only, circuit breaking for flaky providers.
- Jobs are idempotent, have retry limits, and land in a failed-jobs table.
- Migrations are backward compatible for zero-downtime deploys (add, backfill, switch, remove later). Destructive migrations need approval.
- Soft deletes where audit or recovery matters.
- API shape: consistent envelope, correct status codes, 422 with a field-to-message map, pagination meta with `next_cursor`.

## 9. CHOICES and their rules
| choice | rules when chosen |
| --- | --- |
| Classic form POST | PRG pattern (redirect after post), flash messages, old input on validation errors |
| Ajax / fetch | CSRF header, JSON errors with field map, disable submit while pending, handle 401, 403, 419, 422, 429, 500 distinctly |
| Livewire or Inertia | authorize in every action, never trust client props, paginate server-side |
| SSE | authenticate the stream, heartbeat every 15 to 30s, close on logout, disable proxy buffering (`X-Accel-Buffering: no`), one stream per tab |
| WebSocket (Reverb, Soketi, Pusher) | private or presence channels with authorization callbacks, never broadcast personal data on public channels |
| Redis cache | namespaced keys, TTL on every key, cache invalidation on write, never the only copy of data |
| Redis or database queue | idempotent jobs, retries with backoff, Horizon or a supervisor, failed-job alerts |
| Search engine | private API keys server-side, scoped search keys for clients, queued sync |
| JWT or Sanctum tokens | short-lived access tokens, rotating refresh tokens, revoke on logout and password change, abilities scoped |
| S3 or MinIO | private buckets, signed URLs with short expiry, server-side encryption |
| Multi-tenant | tenant id on every tenant table and every query scope; tests that cross-tenant access fails |

## 10. Node.js equivalents
The RULES above apply to every stack. For Node (Express, NestJS, Next.js API routes, Fastify):
- Validation: a schema at every boundary (zod, joi, class-validator). Pick fields explicitly; never pass `req.body` to the database.
- Queries: parameterized (`$1`, `?`) or a builder; Prisma `select` instead of whole rows; never `$queryRawUnsafe` with input. Mongo: cast types, never pass request objects as filters.
- Pagination: Prisma `cursor` + `take`, or keyset `WHERE (created_at, id) < ($1, $2)`.
- Security middleware: `helmet`, a rate limiter (`express-rate-limit`, `@nestjs/throttler`), strict CORS origins, CSRF protection for cookie sessions, `express.json({ limit })`.
- Passwords: argon2 or bcrypt. Tokens: `crypto.randomBytes` or `randomUUID`, never `Math.random`.
- Files and processes: resolve paths against a fixed base; `execFile` with argument arrays, never `exec` with input.
- Checks: `npm audit`, TypeScript strict mode, ESLint, tests with an authorization denial case.

## 11. Done means
- Tests: feature test per endpoint including an authorization denial; unit tests for use cases with branching logic.
- `php -l`, project linters (Pint), static analysis (PHPStan or Larastan), `composer audit`.
- No N+1 on list endpoints (lazy loading prevention on, or query count asserted in a test).
- Report: rules applied, tier choices (pagination type, search tier), indexes added, anything left for infrastructure.
