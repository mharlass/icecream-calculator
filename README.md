# Ice Cream Formula Calculator

Ice Cream Formula Calculator is a Python application for balancing editable ice-cream
recipes. It keeps the ingredient list beside the live formulation results and explains the
main terms before asking the user to set targets.

The application uses:

- **Shiny for Python** for the reactive interface.
- **Shinylive** to run Python in the browser through WebAssembly.
- **GitHub Pages** for static hosting without a Python server.

## What the application does

- Starts with a balanced Ninja CREAMi Deluxe tub batch at 709 ml.
- Includes no-cook dairy, cooked egg-free, egg-yolk custard, and whole-egg custard bases.
- Resizes recipes for Deluxe (709 ml), regular (473 ml), or custom batch sizes.
- Calculates fat, milk solids-not-fat (MSNF), added sugars, total solids, water, gums,
  relative sweetness (POD), and freezing-point depression (PAC).
- Compares every result with the selected Creami/Pacojet or churned target window.
- Provides sliders for fat, sweetness (POD), and freezing-point depression (PAC).
- Optionally solves five ingredient quantities from five formulation targets.
- Scales an entire formula without changing its percentages.
- Adds custom ingredients from a nutrition label or direct per-100 g composition.
- Includes CMC, guar, lambda carrageenan, lecithin, collagen, xanthan, and other
  stabilizer or emulsifier options in the editable ingredient library.
- Provides a cited guide to common stabilizer blends, hydration requirements,
  emulsifiers, and careful small-batch testing.
- Provides process notes for no-cook, cooked dairy, and egg-custard bases.

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

## Project structure

- `dashboard/app.py`: application layout, reactive controls, and browser workflow.
- `dashboard/model.py`: independently tested formulation arithmetic and inverse solver.
- `dashboard/styles.css`: responsive visual system and table layouts.
- `tests/test_model.py`: numerical and failure-mode tests.
- `scripts/export_site.sh`: reproducible Shinylive export.
- `.github/workflows/pages.yml`: GitHub Pages deployment.
