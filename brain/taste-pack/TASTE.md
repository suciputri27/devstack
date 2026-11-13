# Taste Pack

Use this for any UI the project needs: landing pages, portals, panels, kiosks, displays, dashboards, reports, anything. Read `BRAIN.md` first: it is how to think about the screen. The blocks and screens here are quality examples, not limits. Reuse them when they fit; compose new components from tokens and primitives when they do not.

## Start of every project: taste init (once, by the lead)
1. `taste init` in the project root. Interactive questions; agents use `--answers answers.json` with keys name, product, users, mood, mode, density, shape, brand.
2. Open `.taste/compare.html`, compare the 3 candidates (app screen and landing), let the operator choose. Do not choose for the operator.
3. `taste pick <preset>` writes `DESIGN.md`, `.taste/taste.json`, `.taste/tokens.css`, and `public/assets/taste/{taste.css,taste.js,fonts/}` (change with `--assets`).
4. Commit them. After this, every `assemble.py` run inside the project uses the locked preset and tokens automatically.

If `DESIGN.md` or `.taste/taste.json` already exists, never run init again inside a task. A new direction is a LARGE task for the operator.

Presets: `bold-tech`, `editorial-night` (dark); `clean-corporate`, `civic`, `warm-umkm`, `dashboard-pro` (light). Brand color, density, and corner shape are applied on top, and the brand color is shifted automatically until it passes contrast.

## Vision (optional, recommended)
- `taste review <url> [<url>...]` takes desktop and mobile screenshots and, when a vision model is available, returns a scored list of findings with fixes. Report the findings; fix high ones before finishing.
- Configure once per project: `taste vision --base-url http://localhost:20128/v1 --model code-vision --api-key-env NINEROUTER_API_KEY`, or set `TASTE_VISION_BASE_URL`, `TASTE_VISION_MODEL`, `TASTE_VISION_API_KEY`.
- The tool proves the model can see by sending a small red image and checking the answer. Text-only models are skipped and cached, so the check costs one tiny call per model.
- Without vision the tool still saves screenshots to `.ai/screens/`; never claim a visual review happened. Deterministic checks (`taste contrast`, `taste check`) are always required.

## Landing pages

## Workflow
1. Pick a preset from `presets/manifest.json` that fits the audience. Do not mix presets.
2. Copy `content/devstack.bold-tech.json` or `content/konsultan.clean-corporate.json` to `content/<page>.json` in the project and edit only the text and the block order.
3. Write the copy first (rules below), then choose blocks. Each page uses 7 to 12 blocks: `nav` first, `footer` last, one hero.
4. Build: `taste build content/<page>.json public/<page>.html` (add `--preset <name>` to try another preset without editing the file)
5. Run the checks below.
6. Report the command output. Screenshots in `.ai/screens/` are for the operator.

## Hard limits
- Never edit the pack's `core/` or `presets/` inside a task, and never change the locked direction. A new look is a LARGE task for the operator.
- Never invent statistics, testimonials, client names, or prices. Use only facts the operator gave. Missing facts: drop the block or keep the word "Contoh" in the text and list it under open questions.
- New components are welcome, but only with tokens: no color literals, no px or rem for spacing, font size, or radius, no inline styles, no inline event handlers. `taste lint` enforces this.
- `*word*` in assembler content renders as accent emphasis; use it at most once per heading.
- The build fails on banned phrases, em dashes, en dashes, and unrendered tags. Fix the copy, do not work around the check.

## Checks (every UI task)
1. `taste lint` (project views and CSS; pass paths to narrow it)
2. `taste contrast`
3. `taste check <url> --shots .ai/screens`
4. Optional, recommended: `taste review <url>`

## Blocks
| type | use | main fields |
| --- | --- | --- |
| nav | always first | skip_label, menu_label, links[label, href], cta_label, cta_href |
| hero-terminal | tech product, dark presets | badge, title, lead, primary_label/href, secondary_label/href, proof[], terminal_label, terminal_name, lines[kind: cmd, ok, warn, dim; text] |
| hero-statement | corporate, services | eyebrow, title, lead, primary_label/href, secondary_label/href, facts[value, label] (3 items) |
| logos | stack or client types | label, names[] (6 to 10) |
| bento | features, services | id, eyebrow, title, lead, items[size: wide, tall, normal; kicker or icon or log[state: ok, fail; state_label; text]; title; text; tag] |
| steps | process, 3 to 4 steps | id, eyebrow, title, lead, items[title, text] |
| feature-tabs | compare stacks or modes | id, eyebrow, title, lead, items[label, title, text, points[], file, status, code] |
| stats | measurable results | id, title, lead, items[value, prefix, suffix, label], note (source of the numbers) |
| testimonials | real quotes only | id, eyebrow, title, items[featured, quote, name, role, initials] |
| pricing | plans | id, eyebrow, title, lead, switch_label, monthly_label, yearly_label, yearly_save, plans[featured, flag, name, desc, monthly, yearly, monthly_period, yearly_period, features[], cta_label, cta_href] |
| faq | objections | id, eyebrow, title, lead, items[q, a] |
| cta | always before footer | id, title, text, primary_label/href, secondary_label/href |
| footer | always last | tagline, columns[heading, links[label, href]], copyright, note |

Shared: `globals.brand` and `globals.mark` (1 to 3 characters) feed nav and footer. `alt: true` gives a section the alternate background; alternate it every other section.

Bento layout at desktop is a 6-column grid: wide = 4, normal = 2, tall = 2 columns and 2 rows. Rows must add up to 6. Proven orders: wide, tall, normal, normal, normal, wide (6 items) or wide, normal, normal, normal, normal (5 items).

## App screens (panel, forms)
Reference screens: `screens/gallery.html` (every component), `screens/form-sectioned.html` (long form), `screens/form-wizard.html` (multi-step). Built examples: `dist/app-<preset>/`. Reuse this markup for the jobs it covers. For anything else, compose from the primitives in `BRAIN.md` section 3 and write project classes that use only `var(--token)` values.

Load `core/app.css` after `core/base.css`, and `core/app.js` once per page. In Laravel or CI3, put both in the layout, never inline per view.

Components are enhanced native elements, so forms submit normally and server validation stays the source of truth:
| need | markup |
| --- | --- |
| single select | `<select data-ui="select">` with an empty first option; more than 7 options gets search automatically; `data-desc` on an option adds a second line; `optgroup` for groups |
| multi select | `<select multiple data-ui="multiselect" name="x[]">`; `data-max-chips` (default 3) |
| date | `<input type="date" data-ui="date" name min max>`; the server receives `yyyy-mm-dd`; users may type `17/08/2026` |
| upload | `<input type="file" data-ui="upload" accept data-max-mb data-max-files [multiple]>`; label it with `aria-labelledby` |
| text counter | any input or textarea with `maxlength` |
| on or off setting | `.switch` |
| 2 to 4 options with consequences | `.choices` of `.choice` cards inside a `fieldset` with a `legend` |
| 2 to 4 view options | `.segmented` |

Field anatomy, always: `.field` > `label.field__label` (with `<span data-label-text>`, `.field__req` star or `.field__opt` text) > optional `.field__hint` > control. Errors are rendered by `app.js` into `.field__error`.

Choose the form pattern by size:
| fields | pattern |
| --- | --- |
| up to 6 | single `.card` with `.form-grid` and buttons at the bottom |
| 7 to 25, one sitting | `form-sectioned`: `.form-section` per topic, sticky `.form-actions`, `data-draft-key` |
| many fields entered in batches | add the `save_new` button ("Simpan dan tambah lagi") and `data-keep` on fields that repeat between entries |
| sequential decisions, or users who fill it rarely | `form-wizard`: 3 to 5 `.wizard__step` with `data-title`, last step `data-review` |

Form rules:
- `form[data-ui="form"]` gets client validation with Indonesian messages, loading buttons, and dirty state. Remove `data-demo` in real projects.
- `data-draft-key` must be unique per form and per record (`pegawai-baru`, `pegawai-edit-<public_id>`). Drafts live in the browser only; never put secrets in drafted fields; add `data-no-draft` to sensitive fields.
- Submit buttons carry `name="intent"` (`save`, `save_new`, `submit`). The server reads `intent` to decide where to redirect.
- One primary button per form. Destructive actions use `.btn--danger` and a confirmation.
- Labels say what to enter, hints say the format, errors say how to fix it.

## Copy rules (Bahasa Indonesia)
- Lead with the outcome for the reader, then how. One idea per sentence, under 20 words.
- Concrete over generic: numbers the operator gave, named stacks, named steps.
- Use "Anda" for formal audiences. No translated English idioms.
- Banned: "solusi terbaik", "revolusioner", "di era digital", "next level", "game changer", "seamless", "unlock the power", "tingkatkan produktivitas Anda".
- Headlines: 4 to 10 words. Buttons: verb first, 2 to 3 words ("Jadwalkan demo").
- FAQ answers: 1 to 2 sentences, answer first.
