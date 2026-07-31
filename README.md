# Ice Cream Formula Calculator

### ▶ [Open the calculator](https://mharlass.github.io/icecream-calculator/)

**<https://mharlass.github.io/icecream-calculator/>**

The calculator runs entirely in the browser. Nothing to install, no account, no server.

---

Ice Cream Formula Calculator is a Python application for balancing editable ice-cream
and sorbet recipes. It keeps the ingredient list beside the live formulation results and
explains the main terms before asking the user to set targets.

Current version: **0.2.0**

The application uses:

- **Shiny for Python** for the reactive interface.
- **Shinylive** to run Python in the browser through WebAssembly.
- **GitHub Pages** for static hosting without a Python server.

## What the application does

- Starts with a balanced Ninja CREAMi Deluxe tub batch at 709 ml.
- Includes no-cook dairy, cooked egg-free, egg-yolk custard, and whole-egg custard bases.
- Includes a named strawberry sorbet base and a separate experimental fruit-sorbet profile.
- Resizes recipes for Deluxe (709 ml), regular (473 ml), or custom batch sizes.
- Calculates fat, milk solids-not-fat (MSNF), modeled sugars, total solids, water, fiber, gums,
  relative sweetness (POD), and freezing-point depression (PAC).
- Compares every result with the selected Creami/Pacojet, churned, or fruit-sorbet guide.
- Provides targets for fat, milk solids-not-fat, total solids, sweetness (POD), and
  freezing-point depression (PAC), with dairy-only targets hidden for sorbet.
- Optimizes any selected ingredient quantities against any selected applicable targets while
  keeping batch mass fixed and ingredient quantities nonnegative.
- Scales an entire formula without changing its percentages.
- Adds custom ingredients from a nutrition label or direct per-100 g composition.
- Provides guided fruit/purée and chocolate/cocoa entry, including individual fruit sugars
  and separately displayed fiber.
- Includes CMC, guar, lambda carrageenan, lecithin, collagen, xanthan, and other
  stabilizer or emulsifier options in the editable ingredient library.
- Provides a cited guide to common stabilizer blends, hydration requirements,
  emulsifiers, and careful small-batch testing.
- Provides process notes for no-cook, cooked dairy, and egg-custard bases.
- Provides light and dark color modes and a responsive three-step calculator layout.

The CREAMi/Pacojet profiles focus on machines that process a fully frozen container and
can work well with lower-fat recipes than traditional churned ice cream. The fruit-sorbet
profile is explicitly experimental because no reviewed source used here validates one
universal CREAMi- or Pacojet-specific sorbet target window.

## Optimizing a recipe

The optimizer changes only ingredient rows marked **Auto-adjust**. Select any positive
number of rows, open **Optimize selected ingredient weights**, and choose which composition
targets to include. The number of adjustable ingredients does not have to equal the number
of selected targets.

Batch mass is always fixed. Ice-cream profiles can optimize fat, milk solids-not-fat, total
solids, POD, and PAC. The fruit-sorbet profile intentionally omits fat and milk
solids-not-fat, leaving total solids, POD, and PAC as the applicable targets.

Selecting **Optimize selected rows** returns nonnegative ingredient quantities. When the
chosen ingredients cannot satisfy all selected targets simultaneously, the application
returns the closest formulation it can find and reports the remaining target gaps. Rows
that are not marked **Auto-adjust** remain unchanged.

## Custom ingredient persistence

Custom ingredients are kept in the current in-browser Shiny session only. They disappear
when the page is refreshed or reopened, are not shared with another device, and are not
written back to GitHub Pages. Browser-local persistence or portable JSON import/export
would require a separate implementation.

## Run locally

Install the locked environment and start the application:

```bash
uv sync --all-groups
uv run shiny run dashboard/app.py
```

Open <http://127.0.0.1:8000>.

## Validate

```bash
uv run ruff check dashboard tests
uv run python -m py_compile dashboard/app.py dashboard/model.py
uv run python -m pytest -q
```

## Preview the GitHub Pages build

Export the browser-side Python application:

```bash
bash scripts/export_site.sh
uv run python -m http.server 8008 --directory site
```

Open <http://localhost:8008>. The generated `site/` directory is ignored because the
GitHub Actions workflow rebuilds it from source.

The first export downloads and caches the Shinylive runtime. That download is large.
Subsequent exports reuse the cache.

## Publish with GitHub Pages

1. Create a GitHub repository and push this directory to its `main` branch.
2. Open **Settings → Pages** in the repository.
3. Set **Source** to **GitHub Actions**.
4. Push to `main`, or run **Deploy dashboard to GitHub Pages** from the Actions tab.

The included workflow validates the source, exports the Shinylive bundle, and publishes
the generated site.

### Why not a `docs/` folder

Shinylive documents two ways to reach GitHub Pages. The first exports into `docs/`,
commits it, and sets Pages to **Deploy from a branch**. The second keeps the export out of
git and lets GitHub Actions build it. The
[shinylive-example README](https://github.com/wch/shinylive-example) recommends the second
and notes that a committed export is "at least 28MB, for a minimal set of packages"
because it carries Pyodide and every Python wheel the app loads. This project's export is
currently 33 MB across 54 files.

This repository already uses the Actions route, so moving to `docs/` would add work rather
than remove it: every rebuild would write about 33 MB of new binary blobs into git history,
the export would have to be regenerated by hand before each push, and the lint, compile,
and test steps would no longer gate a deploy. The `docs/` layout is the better choice only
when Actions is unavailable. Nothing needs to change here.

## Project structure

- `dashboard/app.py`: application layout, reactive controls, and browser workflow.
- `dashboard/app.js`: mobile navigation behavior for the exported browser app.
- `dashboard/model.py`: independently tested formulation arithmetic and recipe optimizer.
- `dashboard/styles.css`: responsive visual system and table layouts.
- `tests/test_model.py`: numerical and failure-mode tests.
- `scripts/export_site.sh`: reproducible Shinylive export.
- `.github/workflows/pages.yml`: GitHub Pages deployment.
- `research/sorbet_and_complex_ingredients.md`: cited formulation and persistence research.
- `research/responsive_audit.md`: measured phone and tablet layout defects, still open.

## Feedback and contributions

The creator is learning and does not claim authority on ice-cream formulation. The app is
a work in progress. Feedback and suggestions are welcome through
[GitHub issues](https://github.com/mharlass/icecream-calculator/issues), and pull requests
are welcome under the [contribution guide](CONTRIBUTING.md).

See the [changelog](CHANGELOG.md) for release notes. The project is available under the
[MIT License](LICENSE).
