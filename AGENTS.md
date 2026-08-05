# AGENTS.md

Ice Cream Formula Calculator: a Shiny for Python app that balances editable ice-cream
recipes, exported to WebAssembly with Shinylive and published on GitHub Pages.

## Commands

```bash
uv sync --all-groups                                    # locked environment
uv run shiny run dashboard/app.py                       # dev server on :8000
uv run ruff check dashboard tests                       # lint (line-length 100, py312)
uv run python -m py_compile dashboard/app.py dashboard/model.py
uv run python -m pytest -q                              # full suite, sub-second
uv run python -m pytest tests/test_model.py::test_seed_recipe_matches_balanced_reference
bash scripts/export_site.sh                             # rebuild site/ (rm -rf, then export)
uv run python -m http.server 8008 --directory site      # preview the static build
```

`.github/workflows/pages.yml` runs lint, `py_compile`, pytest, then the export and Pages
deploy on every push to `main`. Run the same three validation commands before committing.

## Architecture

- `dashboard/model.py` — the whole formulation engine: ingredient library, composition
  arithmetic, POD/PAC coefficients, diagnostics, the nonnegative recipe optimizer, custom
  ingredient constructors, target windows. Pure Python, no Shiny imports.
- `dashboard/app.py` — one file: five `nav_panel` pages (Overview, Calculator, Ingredients,
  Stabilizers & additives, Process notes) built as functions, plus `server()` holding all
  reactive state (`recipe_state`, `library_state`, and status-message values).
- `dashboard/styles.css` — the visual system; `app.py` pulls it in with `ui.include_css`.
- `tests/test_model.py` — engine only; the UI has no tests.
- `cardamom-lime.md`, `pistachio.md`, `research/` — worked recipes and a cited evidence note
  that feeds the additives tab. Prose deliverables, not code.

Keep new formulation logic in `model.py` and keep it Shiny-free. That separation is what
makes the arithmetic testable and is load-bearing for the browser build.

## Constraints that are easy to violate

**Import style differs between app and tests.** `app.py` uses `from model import ...`, not
`from dashboard.model import ...`, because Shinylive flattens the app directory during
export. Tests use the package path `from dashboard.model import ...`. Never "fix" the import
in `app.py` — it breaks the deployed site while the dev server keeps working.

**Everything runs under Pyodide.** No numpy, scipy, or pandas. The optimizer uses a
pure-Python projected-gradient implementation for exactly this reason. Any new dependency
has to work in the browser and belongs in the `uv.lock` that CI installs with `--frozen`.

**The optimizer keeps batch mass fixed.** `optimize_recipe` may change any positive number
of `RecipeLine`s with `free=True` against any selected subset of the applicable targets. It
keeps quantities nonnegative and reports target gaps when the chosen ingredients cannot
meet every target. Sorbet omits fat and MSNF targets. Presets in `base_recipe` should mark
practical starting rows for auto-adjustment.

**Test values are pinned baselines.** `test_seed_recipe_matches_balanced_reference` asserts
the seed recipe to ~1e-6 (fat 13.496%, POD 111.57, PAC 248.46). Touching
`COMPONENT_FACTORS`, `default_library()`, or `seed_recipe()` moves those numbers. That is
allowed when intended, but re-derive the expected values deliberately and say in the commit
what changed and why — do not adjust an assertion to make a run go green.

**`site/` is generated and gitignored.** `scripts/export_site.sh` deletes and rebuilds it.
Never edit it or commit it. The first export downloads a large Shinylive runtime and caches
it; later exports reuse the cache.

## Domain conventions

- POD (sweetness) and PAC (freezing-point depression) are sucrose-relative: `COMPONENT_FACTORS`
  maps each component to `(POD, PAC)` per 100 g with sucrose at `(100, 100)`, and `Metrics`
  reports both per 1000 g of mix.
- Component keys are fixed vocabulary: `fat`, `msnf`, `water`, `gums`, `other_solids`, `salt`,
  `alcohol`, and the sugar/soluble keys. An ingredient's components should total 100 g per
  100 g; the custom-ingredient constructors infer water by difference when it is passed as 0.
- Target windows live in `target_ranges()`. Creami/Pacojet wants PAC 245–255, churned 220–230;
  fat caps at 15%, total solids 37–42%.
- `diagnose_recipe` encodes the practical guardrails: fat cap, lactose above 10% of the water
  phase (sandiness), dextrose above 50% of the sugar blend, total solids outside 35–45%.
- Ingredient notes carry provenance. Several compositions are estimates anchored to Underbelly
  or approximations from packaging; keep saying so in the `note` field rather than presenting
  an estimate as a measured value.
