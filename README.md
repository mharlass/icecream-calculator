# Ice Cream Formula Calculator

### ▶ [Open the calculator](https://mharlass.github.io/icecream-calculator/)

**<https://mharlass.github.io/icecream-calculator/>**

Balance ice-cream and sorbet recipes in the browser. Nothing to install, no account, no
server.

---

## What it does

- **Shows the balance as you type.** Edit ingredient weights and see fat, milk
  solids-not-fat (MSNF), sugars, total solids, water, fiber, sweetness (POD), and
  freezing-point depression (PAC) update live.
- **Compares against a target window.** Pick a Creami/Pacojet, churned, or fruit-sorbet
  profile and every metric is scored against it.
- **Balances the recipe for you.** Mark the ingredients it may change, pick the targets
  that matter, and the optimizer solves for the weights while holding batch mass fixed.
- **Starts from a working base.** No-cook dairy, cooked egg-free, yolk custard, whole-egg
  custard, and strawberry sorbet, sized for a Ninja CREAMi Deluxe (709 ml), regular
  (473 ml), or any custom batch.
- **Takes your own ingredients.** Add anything from a nutrition label, or use the guided
  entry for fruit purées and chocolate/cocoa.
- **Explains the terms.** Built-in notes on POD and PAC, stabilizer and emulsifier blends
  with sources, and process notes for each base.

The CREAMi/Pacojet targets suit machines that shave a fully frozen puck, which tolerates
lower fat than traditional churned ice cream. The fruit-sorbet profile is marked
experimental because no source reviewed here validates a universal CREAMi-specific sorbet
window.

## Optimizing a recipe

The optimizer only touches rows marked **Auto-adjust**. Select any number of them, open
**Optimize selected ingredient weights**, and choose which targets to include. The count of
adjustable ingredients does not have to match the count of targets.

Batch mass is always fixed and results are nonnegative. Ice-cream profiles can target fat,
MSNF, total solids, POD, and PAC. The fruit-sorbet profile omits fat and MSNF. When the
selected ingredients cannot satisfy every target at once, the app returns the closest
formulation it finds and reports the remaining gaps.

## Custom ingredients are session-only

Ingredients you add live in the current browser session. They disappear on refresh and are
not synced to another device.

## Run locally

```bash
uv sync --all-groups
uv run shiny run dashboard/app.py
```

Open <http://127.0.0.1:8000>.

## Project structure

```
.
├── dashboard/
│   ├── app.py             # Layout, reactive controls, browser workflow
│   ├── app.js             # Mobile navigation for the exported app
│   ├── model.py           # Formulation arithmetic and the optimizer
│   └── styles.css         # Responsive visual system and table layouts
├── tests/
│   └── test_model.py      # Numerical and failure-mode tests
├── scripts/
│   └── export_site.sh     # Reproducible Shinylive export
├── research/              # Cited formulation notes and an open layout audit
├── .github/workflows/
│   └── pages.yml          # GitHub Pages deployment
├── cardamom-lime.md       # Worked example recipe
└── pyproject.toml
```

Built with [Shiny for Python](https://shiny.posit.co/py/), run in the browser through
WebAssembly with [Shinylive](https://shiny.posit.co/py/docs/shinylive.html), and hosted on
GitHub Pages.

## Feedback and contributions

I am learning ice-cream formulation as I go and do not claim authority on it. The app is a
work in progress. Suggestions and corrections are welcome through
[GitHub issues](https://github.com/mharlass/icecream-calculator/issues), and pull requests
are welcome under the [contribution guide](CONTRIBUTING.md).

See the [changelog](CHANGELOG.md) for release notes. Available under the
[MIT License](LICENSE).
