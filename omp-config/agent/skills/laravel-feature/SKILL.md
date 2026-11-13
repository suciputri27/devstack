---
name: laravel-feature
description: Build a new feature or CRUD module in a NEW Laravel project using clean architecture and the repository pattern. Not for existing codebases with a different structure.
---
1. Confirm STANDARD MODE. If the repo has its own structure, stop and switch to mirror mode.
2. Migration: uuid primary key, foreign keys as uuid with constrained(), indexes on filter and sort columns, encrypted columns as text.
3. Model: HasUuids, explicit $fillable, $hidden for sensitive fields, encrypted casts for sensitive data.
4. Domain or Application: repository interface with only the methods the use case needs.
5. Infrastructure: Eloquent repository implementation, bound in a RepositoryServiceProvider.
6. Application: a service or action class per use case, wrapped in DB::transaction when it writes more than once.
7. Presentation: FormRequest (validation and authorize), thin controller, API Resource that never outputs internal ids, Policy registered for the model.
8. Routes: route model binding by uuid, auth and throttle middleware.
9. Tests: feature tests for happy path, validation failure, unauthorized access (IDOR), and not found.
10. Run pint --test, phpstan if present, php artisan test. Report results.
