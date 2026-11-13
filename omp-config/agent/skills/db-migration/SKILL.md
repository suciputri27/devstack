---
name: db-migration
description: Plan and write a safe schema change for PostgreSQL or MySQL, including adding public_id to legacy tables.
---
1. State the engine and version. Write forward and rollback steps.
2. Additive first: add nullable column, backfill in batches, then add constraints and indexes.
3. PostgreSQL: CREATE INDEX CONCURRENTLY outside a transaction for big tables. MySQL 8: check ALGORITHM=INPLACE support.
4. Never drop or rename a column in the same deploy that stops using it.
5. Ask for approval before running anything against a shared database.
