---
name: ci3-feature
description: Add or change a feature in an existing CodeIgniter 3 application while mirroring its current style.
---
1. MIRROR MODE. Open one existing controller, model, and view of a similar feature and copy their structure, naming (Class_model), and response style.
2. Use the Query Builder or $this->db->query($sql, $binds). Never concatenate input.
3. Expose only public_id. If the table lacks it, propose a migration that adds public_id CHAR(36) with a unique index and a backfill.
4. Check ownership of every record loaded from client input before reading or writing it.
5. Escape output with html_escape(). Ajax endpoints return JSON with a fresh CSRF token when csrf_regenerate is on.
6. Validate with form_validation rules, server side, even when the frontend validates.
7. Lint changed files with the PHP version named in the project AGENTS.md.
