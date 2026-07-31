# Changelog

All notable changes to Ice Cream Formula Calculator are documented here.

## [Unreleased]

## [0.2.1] - 2026-07-31

### Added

- `research/responsive_audit.md`, a measured record of open phone and tablet layout
  defects.

### Changed

- Lightened the light-mode blues (`--blue` `#173f6b` to `#22598f`, `--blue-dark` `#092a4b`
  to `#123f6b`). Contrast stays above 7:1 everywhere the tokens are used for text.
- Ingredient quantities now display to 2 decimals instead of 3, with the numeric input
  step matched to 0.01 so entered values stay valid.
- Enlarged the navbar tabs from `0.8rem` to `0.95rem`.
- Set the navbar brand to the full name "Ice Cream Formula Calculator" over two lines.
- Reworded the footer project note.
- Rewrote the README for people arriving from the hosted app: it now leads with the
  calculator link, condenses the feature list to what a user gets from it, and shows the
  repository layout as a file tree. Dropped the maintainer-facing sections. The validation
  commands and the local Pages preview are already documented in `CONTRIBUTING.md` and
  `AGENTS.md`; the one-time Pages setup steps and the note on why the Shinylive export is
  not committed to a `docs/` folder are no longer recorded.

### Fixed

- Dark-mode readability. Five panels used hardcoded light-blue washes that ignored the
  theme, most visibly the alternating base cards, which rendered as near-white slabs
  behind white text. These now use the themed `--panel-tint` and a new `--row-stripe`
  token, and the `--on-accent` token fixes white text on the light accent fills that
  `--blue` and `--teal` become in dark mode. The overview primer card no longer inverts
  into the brightest block on the page. Dark mode now has no text below the WCAG AA
  contrast threshold, measured across all five pages.

## [0.2.0] - 2026-07-31

### Added

- A strawberry sorbet starting base and a separate experimental sorbet target profile.
- Guided fruit/purée and chocolate/cocoa ingredient entry.
- Explicit fiber tracking alongside water, fat, sugars, and other solids.
- A dark-mode control, GitHub and issue links, and an app-wide project disclaimer.
- An MIT license and contribution guide.

### Changed

- Arranged the three calculator steps as adjacent desktop columns, with the optional
  automatic balancer above them and a mobile-first stacked layout at narrower widths.
- Clarified that custom ingredients exist only in the current browser session.
- Updated the application version to 0.2.0.

## [0.1.0] - 2026-07-29

### Added

- Initial Shiny for Python formulation calculator.
- Editable dairy and custard recipes, live composition metrics, and a five-variable solver.
- Shinylive export and GitHub Pages deployment workflow.

[0.2.1]: https://github.com/mharlass/icecream-calculator/releases/tag/v0.2.1
[0.2.0]: https://github.com/mharlass/icecream-calculator/releases/tag/v0.2.0
[0.1.0]: https://github.com/mharlass/icecream-calculator/releases/tag/v0.1.0
