---
name: ui-gate
description: Quality gate after any UI change. Deterministic checks first, optional vision review second. Use before reporting a UI task as done.
---
1. Start or reuse the dev server for the changed pages and note their URLs.
2. Run, and show the real output of each:
   - `taste lint` (or `taste lint <changed view and css paths>`)
   - `taste contrast`
   - `taste check <url> [<url>...] --shots .ai/screens`
3. Fix every failure. At most 2 fix rounds per failing check, then stop and report.
4. Walk the BRAIN.md "before drawing" list for each changed screen: one job, one primary action, every listed state present (loading, empty, error, success, disabled, long content, no permission).
5. Vision is optional: run `taste review <url> [<url>...]`. If it says vision was skipped, do not claim a visual review happened; say the screenshots in .ai/screens/ are ready for the operator.
6. Report: commands with results, states checked, vision result or "skipped", remaining visual risks.
