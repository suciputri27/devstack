# Area: authentication and sessions

Question: can someone log in as another user, keep access after they should lose it, or brute force?
- Passwords: Argon2id or bcrypt via the framework, never md5 or sha1. Reset tokens random, single use, expiring, hashed in the database.
- Login: rate limited per account and IP, generic error message, lockout or delay, audit of failures. OTP and reset endpoints rate limited too.
- Sessions: regenerated on login and privilege change, invalidated on logout and password change, HttpOnly, Secure, SameSite. Remember-me tokens rotated.
- CSRF: on for every state change, Ajax sends the token, no broad `$except` lists. CI3 `csrf_protection` TRUE, `csrf_regenerate` considered.
- API tokens or JWT: short lived, signature verified, `alg` fixed, revocation exists, abilities scoped.
- Account enumeration through login, register, reset messages or timing.
- 2FA if present: cannot be skipped by calling the next step directly.
Evidence: config lines, middleware gaps, or a read-only request showing the behavior.
