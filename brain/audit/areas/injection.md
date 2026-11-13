# Area: injection (SQL, XSS, command, template)

Question: can input change a query, a command, or the page's HTML or JS?
- SQL: raw queries, `whereRaw`, `orderByRaw`, `DB::raw`, `DB::select`, CI3 `$this->db->query`, `->where("...")` strings. Is every user value bound? Are sort columns and directions mapped through an allowlist? `LIKE` patterns escaped for `%` and `_`?
- XSS: Blade `{!! !!}`, CI3 `echo` without `html_escape`, JS `innerHTML`, jQuery `.html()`, `.append()` with data, attribute contexts (`href="{{ $url }}"` allows `javascript:`), JSON embedded in script tags (use `@json` or `json_encode` with hex flags).
- Stored XSS paths: user names, comments, file names, rich text (needs an allowlist sanitizer such as HTMLPurifier).
- Command and code: `exec`, `shell_exec`, `system`, `proc_open`, `eval`, `unserialize`, `preg_replace` with `/e`, dynamic `include` or `require`.
- Template and header injection: user input in mail headers, redirects (`redirect($request->next)` is an open redirect), CSV exports starting with `=`, `+`, `-`, `@` (formula injection).
Evidence: source line, how input reaches it, a payload. Use harmless payloads only (`'`, `<b>t</b>`, `{{7*7}}`).
