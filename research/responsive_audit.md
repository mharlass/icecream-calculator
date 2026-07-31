# Mobile and tablet layout audit

Audit of `dashboard/app.py` + `dashboard/styles.css` at phone and tablet widths.
Date: 2026-07-31. Branch: `feature/site-polish`.

This report lists defects only. None of them are fixed in this branch; the colour and
typography work committed alongside it is separate.

## Method

Headless Chromium (Playwright 1.58) against the local dev server, five pages
(Overview, Calculator, Ingredients, Stabilizers & additives, Process notes) at seven
viewports: 375×812, 390×844, 414×896, 768×1024, 834×1112, 1024×1366, 1180×820.
Both colour themes. Measurements are computed from `getBoundingClientRect()` and
`document.documentElement.scrollWidth`, not read off screenshots.

Two things were checked and are **clean**: no page scrolls horizontally at any tested
width, and no element escapes the viewport outside a deliberate `overflow-x: auto`
container. The `.table-scroll` wrappers on the ingredient library and additive tables
work as intended.

## Defects

### 1. Navigation bar wraps to two rows from 768 px to 957 px — high

The navbar is `navbar-expand-md`, so Bootstrap stops collapsing it into the hamburger at
768 px. The nav content needs about 958 px, so between those two points it expands and
then wraps.

Measured navbar height (76 px is the correct single-row height):

| Viewport width | Navbar height | State |
| --- | --- | --- |
| 768–800 px | 108 px | nav links themselves split across two rows |
| 834–920 px | 108–111 px | links on one row, GitHub + theme toggle pushed to row two |
| 925–955 px | 111 px | links on one row, GitHub + theme toggle pushed to row two |
| 958 px and up | 76 px | correct |

The upper bound moved from 919 px to 957 px when the tab font size went from `0.8rem` to
`0.95rem`. Raising the tab size widens the menu, so it postpones the point at which the
row fits. The underlying cause is unchanged.

This covers iPad portrait (768) and iPad Air/Pro portrait (834), which is the most likely
tablet case. The brand lockup ends up vertically stranded next to a two-row menu.

Fix: keep the navbar collapsed until it actually fits, by overriding the `navbar-expand-md`
rules in a `@media (max-width: 957.98px)` block so `.navbar-collapse` stays hidden and
`.navbar-toggler` stays visible. `dashboard/app.js` already handles closing the collapse
after a tab click, so the hamburger path is proven.

### 2. Auto-adjust checkbox renders as a 15 × 36 px bar — high

`dashboard/styles.css`:

```css
.formula-table input,
.formula-table .selectize-input {
  min-height: 36px;
  font-size: 0.78rem;
}
```

`min-height: 36px` is meant for the quantity text field but also matches the auto-adjust
`input[type=checkbox]`, which has a fixed width. Every checkbox in the ingredient table
measures **15 × 36 px** instead of roughly 16 × 16. Checked rows read as solid blue
vertical bars and unchecked rows as empty outlines, so the column looks like a progress
indicator rather than a set of checkboxes.

This is not viewport-dependent — it reproduces at 375 px and at 1440 px — but it is worst
on tablet, where the column is wide and the bars are the most prominent thing in the row.

Fix: scope the rule, e.g. `.formula-table input:not([type="checkbox"])`.

### 3. Ingredient column is crushed at 768–834 px while auto-adjust takes triple its width — high

Measured cell widths of a `.formula-table` row at 768 px:

| Column | Declared | Actual |
| --- | --- | --- |
| `#` | 40 px | 40 px |
| Ingredient | (auto) | **142 px** |
| Quantity · g | 124 px | 124 px |
| Auto-adjust | 105 px | **312 px** |
| Remove | 40 px | 42 px |

The table has no `table-layout: fixed`, so the declared widths are hints only. The
auto-adjust cell holds a checkbox plus an unconstrained "Allow" label and wins the
surplus, leaving the ingredient select at 142 px. Consequences at 768 px and 834 px:

- Longer names wrap to two lines ("Whole milk · 3.5% fat", "Soy lecithin powder",
  "Lambda carrageenan"), so row heights are uneven.
- On single-line-but-tight names the select caret overlaps the text: "Cream · 35% fat▾",
  "Nonfat dry milk▾".
- Roughly 170 px of dead space sits between "Allow" and the remove icon.

Fix: `table-layout: fixed` plus an explicit ingredient column width, or cap the
auto-adjust cell and let the ingredient select take `width: 100%`.

### 4. "On this page" occupies a grid cell in the table of contents at 681–900 px — medium

At that range `.method-toc` becomes `grid-template-columns: repeat(3, minmax(0, 1fr))`,
but the `<strong>On this page</strong>` label is a grid item like the links. It takes the
first cell, so the first link starts in column two and the list reads:

```
On this page   |  No-cook base    |  Cooked egg-free base
Egg custard    |  Fruit sorbet    |  CREAMi processing
Sources        |                  |
```

The heading looks like a link and the sequence is hard to scan.

Fix: give the label `grid-column: 1 / -1`.

### 5. Tap targets below the 44 px minimum — medium

Smallest interactive elements at 375 px, by kind:

| Element | Count | Smallest measured |
| --- | --- | --- |
| Citation superscripts (`.citation a`, additives page) | 39 | **5 × 9 px** |
| Footer links | 4 | 39 × 18 px |
| Reference list links (`.source-list`, `.reference-list`) | 7 | 113 × 16 px |
| Table-of-contents links (`.method-toc a`) | 6 | 138 × 17 px |
| Auto-adjust checkboxes | 16 | 15 × 17 px |
| Row remove buttons (`.row-remove`) | 11 | 30 × 30 px |

The citation superscripts are the serious one: 39 links at roughly 5 × 9 px on the
additives page are effectively unhittable on a touch screen, and they sit inline in body
text so neighbouring targets are close together.

Fix: add vertical padding plus a transparent hit area (`::after` inset overlay, or
`min-height: 44px` with negative margins) on inline links at touch widths; enlarge
`.row-remove` to 44 px and the checkbox to at least 24 px below 900 px.

### 6. Dead vertical space in the guided ingredient cards below 900 px — low

`.guided-ingredient-card > p { min-height: 72px; }` and
`.guided-ingredient-card > .field-note { min-height: 50px; }` exist to keep the two cards
aligned while they sit side by side. Below 900 px `.guided-ingredient-grid` collapses to a
single column, so the equalisation has nothing to align against and only adds a visible
gap under the intro paragraph and under the field note.

Fix: drop both `min-height` values inside the `max-width: 900px` block.

## Checked and acceptable

- Formula table card layout below 680 px. The `display: block` + grid re-layout with
  `data-label` pseudo-element headings works and stays inside the viewport.
- Balance cards, solver controls and the custom-ingredient grid collapse cleanly at every
  breakpoint.
- The additive and ingredient library tables keep their `min-width` and scroll inside
  `.table-scroll` rather than stretching the page.
- Both `.metric-primer` and the base overview cards reflow correctly at 375 px.
- No horizontal page scroll at any tested viewport, in either theme.
