# Contributing

Feedback, recipe observations, bug reports, and suggestions are welcome.

## Open an issue

Before opening a new issue, please search the
[existing issues](https://github.com/mharlass/icecream-calculator/issues) for a similar
report. If none exists, open a new issue and include:

- what you expected and what happened;
- the base, target profile, ingredient values, and browser you used;
- steps that reproduce the problem;
- a screenshot when the issue concerns layout or a displayed result;
- the source of any proposed ingredient composition or formulation coefficient.

Do not include private information or copyrighted recipe text that you cannot share.

## Pull requests

Pull requests are welcome. Keep changes focused and explain the reason for any formulation
assumption. For changes to ingredient data, target ranges, or POD/PAC coefficients, cite the
source and describe whether the value is measured, supplied by a manufacturer, or estimated.

Set up and validate the project with:

```bash
uv sync --all-groups
uv run ruff check dashboard tests
uv run python -m py_compile dashboard/app.py dashboard/model.py
uv run python -m pytest -q
```

For interface changes, also rebuild and inspect the static Shinylive export:

```bash
bash scripts/export_site.sh
uv run python -m http.server 8008 --directory site
```

By contributing, you agree that your contribution may be distributed under the
[MIT License](LICENSE).
