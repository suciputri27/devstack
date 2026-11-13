# Design brain

Read this once per UI task, together with the project's DESIGN.md. It is how to think, not a catalog. Build any feature the project needs. The blocks and screens in this pack are quality examples, not limits.

## 1. Before drawing anything
- Name the screen type (section 4) and the one job of the screen. Write it as one line in the plan: "Panel petugas: call the next ticket fast."
- List who uses it, where (desk, phone, TV across a room, kiosk standing), and how often (every minute, once a year).
- Decide the primary action. Exactly one per view. Everything else is secondary or quiet.
- List the states that will exist: loading, empty, error, success, disabled, long content, no permission, offline if relevant.

## 2. Principles
**Hierarchy.** One focal point per view: the primary number, the primary action, or the main message. Size, weight, and color go to it first. If two things compete, shrink one.
**Rhythm.** Use only the space tokens. Related items sit closer (space-2 to space-3) than unrelated groups (space-6 and up). Equal gaps everywhere means no grouping.
**Alignment.** One left edge per column. Numbers right-aligned and tabular. Labels above fields. Avoid centering anything longer than two lines.
**Density by frequency.** Daily expert users get compact tables and keyboard paths. Occasional public users get large targets, one task per screen, plain words.
**Color with meaning.** Accent marks the primary action and the current location. Status colors only for status. Never decorate with status colors. Large areas stay neutral.
**Type.** At most two families (the preset's). Display font for page titles and big numbers, body font for everything else. Body text 60 to 75 characters per line.
**Motion.** Only to explain change: a panel opening, an item added, a number updated. 150 to 300ms. Respect reduced motion.
**Honesty.** Show real data shapes: long names, empty lists, 0 values, 10,000 rows. Design for the worst case, then the typical case looks calm.
**Anti-generic.** No gradient backgrounds without a reason, no emoji icons, no grid of identical cards as the main content, no glassmorphism decoration, no stock hero illustrations. Structure and typography carry the design.

## 3. Composition with primitives
Build new components from tokens and these primitives in `core/app.css`. Do not add colors, sizes, radii, or shadows outside the tokens.
| primitive | use |
| --- | --- |
| `.l-stack` (+ `--2` to `--8`) | vertical flow with a fixed gap |
| `.l-cluster` | items in a row that wrap: buttons, badges, filters |
| `.l-grid` (`--2` `--3` `--4` or `--auto`) | responsive columns |
| `.l-split` | content plus side panel; collapses on mobile |
| `.l-sidebar-detail` | list on the left, detail on the right |
| `.l-center` | readable centered column for long text or single tasks |
| `.surface` (`--raised` `--sunken` `--accent`) | any box; replaces ad hoc cards |
| `.badge` (`--accent` `--success` `--warning` `--danger` `--neutral`) | status and counts |
| `.stat` | label, big value, delta |
| `.list` / `.list__item` | rows with leading, content, trailing |
| `.table` (+ `--compact`) | data tables, sticky header, numeric cells `.num` |
| `.empty` | empty state: icon, title, text, action |
| `.skeleton` | loading placeholders |
| `.display-xl` `.display-l` | huge numbers or words for TV and kiosk screens |
| `.kbd`, `.divider`, `.text-muted`, `.text-num` | small helpers |
Existing components (`.btn`, `.field`, `data-ui` controls, `.form-actions`, `.wizard`, `.notice`, `.toast`, app shell) remain the default for their jobs.

A new component is fine when no existing one fits. Write it as a small class block in the project's own CSS file, using only `var(--token)` values, and name it after its job (`.ticket`, `.counter-card`), not its look.

## 4. Screen recipes
**Public landing or portal.** Clear statement of who it serves and the top 3 tasks above the fold. Services as a scannable list or grid of task links, not marketing cards. News and announcements as a dated list with the newest first. Contact, hours, and location always reachable from the footer.
**Kiosk or touch screen (standing user).** One task per screen, 2 to 6 giant choices (min 72px high), large text (step-2 and up), no hover-only affordances, a visible "back" and "start over", timeout back to start. High contrast, no small print.
**Display or TV (read from far).** Read at 5 meters: the key number uses `.display-xl`, current item highlighted with accent, next items listed smaller. No interaction, no scrolling, auto-refresh, clock visible. Dark preset or high-contrast surfaces.
**Operator panel (daily expert).** Primary action fixed in a predictable spot, keyboard shortcut shown with `.kbd`. Current item large, queue or history compact. Status badges, not colored paragraphs. Confirm only destructive actions.
**List of records.** Search and the 2 to 3 most used filters on top, bulk actions appear on selection, table on desktop, list on mobile. Empty state explains how to add the first record. Pagination or infinite load with a count.
**Record detail.** Title and status at top, primary action top right, facts in a two-column definition list, related items and activity below. Edit opens the form pattern.
**Form.** Use the form patterns in TASTE.md (single card, sectioned with draft, wizard).
**Dashboard.** Top row: 3 to 5 `.stat` with the question each answers. Then one main chart or table that drives a decision. Everything else below the fold. Every number shows its period.
**Report or print.** `.l-center` width, serif or body font, page header with title, period, and generated date, tables with `.num`, no navigation or interactive controls, `@media print` hides the shell.
**Auth (login, reset).** Single centered task, product name, one primary button, error messages in place, no decoration that delays the task.
**Empty, error, offline.** Say what happened, why if known, and the next step as a button. Never a blank area.

## 5. Copy
Bahasa Indonesia, plain and specific. Labels name the data, hints show the format, errors say how to fix it, buttons start with a verb. Follow the Voice section in DESIGN.md. No em dashes.

## 6. Done means
- `taste lint`, `taste contrast`, and `taste check` pass.
- Every state from step 1 exists.
- With a vision model configured, `taste review` has no high findings. Without one, screenshots are in `.ai/screens/` for the operator.
