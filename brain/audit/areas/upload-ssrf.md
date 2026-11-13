# Area: uploads, files, and SSRF

Question: can a file or URL give an attacker code execution, other users' files, or access to internal services?
- Uploads: MIME checked by content, extension allowlist, size limit, random stored name, stored outside the public root or served by an authorized route, images re-encoded if displayed. No `getClientOriginalName()` in paths. CI3 `upload_path` outside web root, `allowed_types` strict, `encrypt_name` TRUE.
- Downloads: path traversal (`../`) in file parameters, authorization before serving, signed URLs expire.
- Archives: zip slip on extraction, zip bombs.
- SSRF: any server-side fetch of a user-supplied URL (webhooks, link previews, imports, PDF renderers). Needs a host allowlist, scheme allowlist (https), and blocking of private and link-local ranges, including after redirects.
- XXE: XML parsing with external entities disabled.
- Image processing libraries on untrusted input (ImageMagick policies).
Evidence: the code path from request to filesystem or network call.
