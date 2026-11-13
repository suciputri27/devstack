# Area: business logic

Question: can a valid user break the rules of the business, even without a classic vulnerability?
- Prices, totals, discounts, quotas, stock, and points calculated on the server, never trusted from the client.
- State machines: can a step be skipped (pay, approve, verify) by calling a later endpoint directly? Can a cancelled or completed record be changed?
- Race conditions: double submit, two requests at once on stock, balance, queue numbers, coupons. Look for missing transactions, `lockForUpdate`, unique constraints, idempotency keys.
- Limits: per-user limits enforced server-side; pagination and export caps; negative or huge numbers; decimals on integer fields.
- Workflow roles: can the requester also approve their own request?
- Notifications and emails: can a user trigger messages to arbitrary addresses (spam relay)?
- Time: deadlines checked server-side in the right time zone.
Evidence: the endpoint, the missing check, and the step-by-step abuse.
