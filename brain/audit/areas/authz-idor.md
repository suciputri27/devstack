# Area: authorization and IDOR

Question: can a user read or change something that is not theirs, or do something their role forbids?
- List every route that takes an identifier (route params, query, body, hidden fields, Ajax payloads). For each, trace to the query: is it scoped by owner or tenant, or checked by a Policy or Gate before use?
- Laravel: `authorize()`, `can` middleware, `Gate::`, policies registered, `->where('user_id', ...)`, global scopes. Look for `find($id)`, `findOrFail($request->...)`, route model binding without `scopeBindings()` or a policy.
- CI3: every controller method that loads a record by id must check ownership or role explicitly. Check `_remap`, base controllers, and hooks that may (or may not) enforce login.
- Admin routes: middleware present on the group? Any admin action reachable from a non-admin route?
- Mass actions and exports: are filters applied server-side for the current user?
- Integer ids exposed (URLs, `data-id`, JSON) make enumeration trivial; note them.
- Horizontal (user to user) and vertical (user to admin) escalation, plus tenant boundaries in multi-tenant apps.
Evidence: the route, the controller line, and the missing check. With a dev URL: two test accounts, request A's record with B's session, read-only.
