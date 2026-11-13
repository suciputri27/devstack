# Project facts
- Framework: (contoh: Laravel 12 on PHP 8.3, CodeIgniter 3.1.13 on PHP 7.4 (run php with: php7.4), atau Node 22 + Express/NestJS/Next.js)
- Mode: MIRROR atau STANDARD
- Style reference files: (2 sampai 3 file contoh yang paling rapi)
- Database: (PostgreSQL 16 / MySQL 8), migrations: (lokasi dan formatnya)
- Public identifier column: (uuid id / public_id)

# Commands
- Lint: git diff --name-only --diff-filter=ACM | grep '\.php$' | xargs -r -n1 php -l
- Format check: (contoh: ./vendor/bin/pint --test)
- Static analysis: (contoh: ./vendor/bin/phpstan analyse)
- Tests: (contoh: php artisan test)
- Run: (contoh: php artisan serve --port=8001)

# Do not touch
- (contoh: system/, application/third_party/, vendor/, public/build/)
