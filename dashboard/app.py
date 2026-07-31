"""Ice Cream Formula Calculator: a practical formulation application."""

from __future__ import annotations

from pathlib import Path

from model import (
    BASE_PRESET_INFO,
    SOLUBLE_COMPONENT_LABELS,
    TARGET_PROFILE_INFO,
    FormulationError,
    Ingredient,
    RecipeLine,
    Targets,
    base_recipe,
    calculate_recipe,
    default_library,
    diagnose_recipe,
    ingredient_from_composition,
    ingredient_from_fruit_composition,
    ingredient_from_nutrition_label,
    ingredient_pac_coefficient,
    ingredient_pod_coefficient,
    optimize_recipe,
    scale_recipe,
    target_ranges,
)
from shiny import App, Inputs, Outputs, Session, reactive, render, ui

APP_DIR = Path(__file__).parent
APP_VERSION = "0.2.0"
REPOSITORY_URL = "https://github.com/mharlass/icecream-calculator"
MAX_RECIPE_ROWS = 24
BATCH_MASSES = {
    "deluxe": 709.0,
    "regular": 473.0,
}


def icon(name: str) -> ui.HTML:
    """Return a small inline icon."""

    paths = {
        "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
        "check": '<path d="m5 12 4 4L19 6"/>',
        "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
        "plus": '<path d="M12 5v14M5 12h14"/>',
        "scale": '<path d="M4 19h16M6 16l4-9h4l4 9M8 12h8"/>',
        "spark": '<path d="m12 3 1.4 4.1L17.5 8.5l-4.1 1.4L12 14l-1.4-4.1-4.1-1.4 4.1-1.4z"/>',
        "trash": '<path d="M4 7h16M9 7V4h6v3M7 7l1 13h8l1-13"/>',
    }
    return ui.HTML(f'<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">{paths[name]}</svg>')


def ingredient_choices(library: dict[str, Ingredient]) -> dict[str, dict[str, str]]:
    """Return ingredient choices grouped by their reader-facing category."""

    grouped: dict[str, dict[str, str]] = {}
    for ingredient_id, ingredient in library.items():
        grouped.setdefault(ingredient.category, {})[ingredient_id] = ingredient.name
    return grouped


def page_intro(eyebrow: str, title: str, description: str) -> ui.Tag:
    """Create a compact page heading."""

    return ui.tags.header(
        ui.div(eyebrow, class_="eyebrow"),
        ui.h1(title),
        ui.p(description, class_="page-lede"),
        class_="page-intro",
    )


def app_footer() -> ui.Tag:
    """Return the application-wide project note and links."""

    return ui.tags.footer(
        ui.div(
            ui.div(
                ui.div(f"Ice Cream Formula Calculator · v{APP_VERSION}", class_="footer-title"),
                ui.p(
                    "I am learning ice-cream formulation as I go, so treat the numbers here "
                    "as a starting point rather than settled advice. The app is still taking "
                    "shape, and corrections or suggestions are genuinely useful."
                ),
            ),
            ui.div(
                ui.tags.a(
                    "GitHub",
                    href=REPOSITORY_URL,
                    target="_blank",
                    rel="noopener noreferrer",
                ),
                ui.tags.a(
                    "Feedback & issues",
                    href=f"{REPOSITORY_URL}/issues",
                    target="_blank",
                    rel="noopener noreferrer",
                ),
                ui.tags.a(
                    "Changelog",
                    href=f"{REPOSITORY_URL}/blob/main/CHANGELOG.md",
                    target="_blank",
                    rel="noopener noreferrer",
                ),
                ui.tags.a(
                    "MIT license",
                    href=f"{REPOSITORY_URL}/blob/main/LICENSE",
                    target="_blank",
                    rel="noopener noreferrer",
                ),
                class_="footer-links",
            ),
            class_="app-footer-inner",
        ),
        class_="app-footer",
    )


def term_row(term: str, name: str, explanation: str) -> ui.Tag:
    """Create one glossary row."""

    return ui.div(
        ui.div(ui.strong(term), ui.span(name)),
        ui.p(explanation),
        class_="term-row",
    )


def metric_primer() -> ui.Tag:
    """Explain the three primary formulation controls before use."""

    return ui.tags.aside(
        ui.div(
            icon("info"),
            ui.div(
                ui.div("Read this first", class_="eyebrow"),
                ui.h2("Three numbers guide the recipe"),
            ),
            class_="primer-heading",
        ),
        term_row(
            "Fat",
            "richness and body",
            "The percentage of the mix that is milk fat or other declared fat. More is not "
            "always better. Too much can feel heavy or greasy.",
        ),
        term_row(
            "POD",
            "relative sweetness",
            "A sucrose-equivalent sweetness index. It helps compare sugar blends that taste "
            "more or less sweet at the same weight.",
        ),
        term_row(
            "PAC",
            "freezing-point depression",
            "A sucrose-equivalent freezing index. A higher value generally gives a softer "
            "frozen mix at the same freezer temperature.",
        ),
        ui.p(
            "POD and PAC are guide values, not percentages. This calculator uses a "
            "mix-normalized index where 100 g sucrose in a 1,000 g mix equals 100.",
            class_="primer-note",
        ),
        class_="metric-primer",
    )


def landing_page() -> ui.Tag:
    """Return a concise orientation page."""

    return ui.div(
        ui.tags.section(
            ui.div(
                ui.div("Ice cream recipe calculator", class_="eyebrow"),
                ui.h1("Create the recipe"),
                ui.p(
                    "Choose an ice-cream or sorbet base, set the batch size, and adjust "
                    "ingredients by weight. The calculator updates sweetness, freezing "
                    "behavior, water, fat, fiber, and solids as you work.",
                    class_="home-lede",
                ),
                ui.div(
                    ui.input_action_button(
                        "start_building",
                        ui.span("Start a recipe", icon("arrow")),
                        class_="button button-primary button-large",
                    ),
                    ui.input_action_button(
                        "open_method",
                        "Read the process notes",
                        class_="button button-quiet button-large",
                    ),
                    class_="home-actions",
                ),
                ui.p(
                    "Default: no-cook dairy base · Ninja CREAMi Deluxe tub · 709 ml. "
                    "CREAMi and Pacojet profiles are intended for machines that process a "
                    "fully frozen container and can work well with lower-fat recipes than "
                    "traditional churned ice cream.",
                    class_="default-note",
                ),
                class_="home-copy",
            ),
            metric_primer(),
            class_="home-grid",
        ),
        ui.tags.section(
            ui.div(
                ui.div("Starting bases", class_="eyebrow"),
                ui.h2("Begin with the process you plan to use"),
                ui.p(
                    "Each starting formula is editable. Loading a base does not lock you into "
                    "its ingredients or targets.",
                    class_="section-lede",
                ),
            ),
            ui.div(
                *[
                    ui.tags.article(
                        ui.h3(info["name"]),
                        ui.p(info["description"]),
                        ui.tags.small(info["process"]),
                    )
                    for info in BASE_PRESET_INFO.values()
                ],
                class_="base-overview-grid",
            ),
            class_="home-section",
        ),
        ui.tags.section(
            ui.div("Basic workflow", class_="eyebrow"),
            ui.h2("Use the calculator in three passes"),
            ui.tags.ol(
                ui.tags.li(
                    ui.span("1"),
                    ui.div(
                        ui.h3("Choose a base and batch size"),
                        ui.p(
                            "Load a dairy, custard, or fruit-sorbet starting formula."
                        ),
                    ),
                ),
                ui.tags.li(
                    ui.span("2"),
                    ui.div(
                        ui.h3("Edit the ingredient weights"),
                        ui.p("Add, remove, or replace ingredients. Results update automatically."),
                    ),
                ),
                ui.tags.li(
                    ui.span("3"),
                    ui.div(
                        ui.h3("Compare with your targets"),
                        ui.p(
                            "Use the sliders as goals, or optimize any selected ingredient rows."
                        ),
                    ),
                ),
                class_="workflow-list",
            ),
            class_="home-section workflow-section",
        ),
        class_="page-shell landing-page",
    )


def builder_page() -> ui.Tag:
    """Return the main recipe-building page."""

    base_choices = {preset_id: info["name"] for preset_id, info in BASE_PRESET_INFO.items()}
    target_choices = {
        profile_id: info["name"] for profile_id, info in TARGET_PROFILE_INFO.items()
    }
    return ui.div(
        page_intro(
            "Calculator",
            "Build a batch",
            "Load a starting point, then work directly in the ingredient list. The balance "
            "panel stays visible and updates when a quantity changes.",
        ),
        ui.tags.details(
            ui.tags.summary(
                ui.div(
                    ui.div("Optional", class_="eyebrow"),
                    ui.h2("Optimize selected ingredient weights"),
                ),
                ui.span("Open controls", class_="details-action"),
            ),
            ui.div(
                ui.p(
                    "Batch mass stays fixed. Mark the ingredients the optimizer may change, "
                    "then choose the targets it should pursue. Any number of ingredient rows "
                    "may be selected. If the combination cannot meet every target, the closest "
                    "nonnegative formula is returned and the remaining gaps are reported."
                ),
                ui.div(
                    ui.panel_conditional(
                        "input.target_profile !== 'Fruit sorbet · experimental'",
                        ui.div(
                            ui.input_checkbox(
                                "optimize_fat",
                                "Include fat",
                                value=True,
                            ),
                            ui.input_slider(
                                "target_fat",
                                "Fat target · %",
                                min=0,
                                max=20,
                                value=13.5,
                                step=0.1,
                            ),
                            ui.p("Richness and body.", class_="control-help"),
                            class_="optimizer-target",
                        ),
                    ),
                    ui.panel_conditional(
                        "input.target_profile !== 'Fruit sorbet · experimental'",
                        ui.div(
                            ui.input_checkbox(
                                "optimize_msnf",
                                "Include milk solids-not-fat",
                                value=True,
                            ),
                            ui.input_numeric(
                                "target_msnf",
                                "Milk solids-not-fat target · %",
                                value=11.5,
                                min=0,
                                max=20,
                                step=0.1,
                                width="100%",
                            ),
                            ui.p("Milk proteins, lactose, and minerals.", class_="control-help"),
                            class_="optimizer-target",
                        ),
                    ),
                    ui.div(
                        ui.input_checkbox(
                            "optimize_solids",
                            "Include total solids",
                            value=True,
                        ),
                        ui.input_slider(
                            "target_solids",
                            "Total solids target · %",
                            min=20,
                            max=45,
                            value=39,
                            step=0.5,
                        ),
                        ui.p(
                            "Fat, sugars, milk solids, fruit, fiber, and other solids.",
                            class_="control-help",
                        ),
                        class_="optimizer-target",
                    ),
                    ui.div(
                        ui.input_checkbox(
                            "optimize_pod",
                            "Include sweetness",
                            value=True,
                        ),
                        ui.input_slider(
                            "target_pod",
                            "Sweetness target · POD",
                            min=70,
                            max=240,
                            value=112,
                            step=1,
                        ),
                        ui.p("Higher means sweeter.", class_="control-help"),
                        class_="optimizer-target",
                    ),
                    ui.div(
                        ui.input_checkbox(
                            "optimize_pac",
                            "Include freeze softness",
                            value=True,
                        ),
                        ui.input_slider(
                            "target_pac",
                            "Freeze softness target · PAC",
                            min=180,
                            max=380,
                            value=248,
                            step=1,
                        ),
                        ui.p("Higher generally freezes softer.", class_="control-help"),
                        class_="optimizer-target",
                    ),
                    class_="target-slider-grid",
                ),
                ui.div(
                    ui.input_action_button(
                        "solve_formula",
                        ui.span(icon("spark"), "Optimize selected rows"),
                        class_="button button-primary",
                    ),
                    class_="solver-actions",
                ),
                ui.output_ui("solver_status"),
                class_="solver-content",
            ),
            class_="surface solver-surface",
        ),
        ui.div(
            ui.tags.section(
                ui.div(
                    ui.div("1", class_="step-number"),
                    ui.div(
                        ui.h2("Choose the starting point"),
                        ui.p("Loading a base replaces the current ingredient list."),
                    ),
                    class_="section-heading",
                ),
                ui.div(
                    ui.input_select(
                        "base_style",
                        "Base style",
                        choices=base_choices,
                        selected="no_cook",
                        width="100%",
                    ),
                    ui.input_select(
                        "batch_size",
                        "Batch size",
                        choices={
                            "deluxe": "Deluxe CREAMi tub · 709 ml",
                            "regular": "Regular CREAMi tub · 473 ml",
                            "custom": "Custom batch mass",
                        },
                        selected="deluxe",
                        width="100%",
                    ),
                    ui.panel_conditional(
                        "input.batch_size === 'custom'",
                        ui.input_numeric(
                            "custom_batch_mass",
                            "Custom batch mass · g",
                            value=750,
                            min=100,
                            max=5000,
                            step=10,
                            width="100%",
                        ),
                    ),
                    ui.input_select(
                        "target_profile",
                        "Recipe target",
                        choices=target_choices,
                        selected="Creami / Pacojet",
                        width="100%",
                    ),
                    class_="setup-controls",
                ),
                ui.output_ui("base_summary"),
                ui.div(
                    ui.input_action_button(
                        "load_base",
                        "Load base and batch size",
                        class_="button button-primary",
                    ),
                    ui.input_action_button(
                        "resize_recipe",
                        ui.span(icon("scale"), "Resize current recipe"),
                        class_="button button-quiet",
                    ),
                    class_="setup-actions",
                ),
                ui.p(
                    "Tub sizes are volume labels. The preset uses the same number as a practical "
                    "starting mass in grams. Weigh the mix and never fill above the tub's MAX line.",
                    class_="field-note",
                ),
                class_="surface setup-surface",
            ),
            ui.tags.section(
                ui.div(
                    ui.div(
                        ui.div("2", class_="step-number"),
                        ui.div(
                            ui.h2("Edit the ingredients"),
                            ui.p(
                                "All quantities are grams in the complete batch. Ingredient "
                                "choices are grouped by their role in the recipe."
                            ),
                        ),
                        class_="section-heading",
                    ),
                    class_="section-heading-row",
                ),
                ui.output_ui("formula_table"),
                ui.div(
                    ui.div(
                        ui.input_selectize(
                            "add_ingredient",
                            "Add an ingredient",
                            choices={},
                            width="100%",
                            options={"placeholder": "Search by name or browse a group"},
                        ),
                        class_="add-field add-field-wide",
                    ),
                    ui.div(
                        ui.input_numeric(
                            "add_grams",
                            "Quantity · g",
                            value=10,
                            min=0,
                            step=0.1,
                            width="100%",
                        ),
                        class_="add-field",
                    ),
                    ui.input_action_button(
                        "add_line",
                        ui.span(icon("plus"), "Add"),
                        class_="button button-secondary add-button",
                    ),
                    class_="add-ingredient-bar",
                ),
                class_="surface formula-surface",
            ),
            ui.tags.aside(
                ui.div(
                    ui.div("3", class_="step-number"),
                    ui.div(
                        ui.h2("Check the balance"),
                        ui.p("Current values are compared with the active recipe targets."),
                    ),
                    class_="section-heading",
                ),
                ui.output_ui("results_panel"),
                class_="surface result-surface",
            ),
            class_="builder-steps-grid",
        ),
        ui.tags.section(
            ui.div("Glossary", class_="eyebrow"),
            ui.h2("What the numbers mean"),
            ui.div(
                term_row(
                    "Fat",
                    "percent of total mix",
                    "Contributes richness, lubrication, and body. The ingredient data determine "
                    "which declared fats are included.",
                ),
                term_row(
                    "POD",
                    "relative sweetness",
                    "Potere Dolcificante. A sucrose-equivalent index for perceived sweetness. "
                    "Sucrose and dextrose can have different POD and PAC effects.",
                ),
                term_row(
                    "PAC",
                    "freezing-point depression",
                    "Potere Anti-Congelante. A sucrose-equivalent index for how strongly dissolved "
                    "ingredients lower the freezing point. Higher PAC generally means a softer mix.",
                ),
                term_row(
                    "MSNF",
                    "milk solids-not-fat",
                    "Milk proteins, lactose, and minerals after milk fat and water are excluded. "
                    "They add body but too much lactose can become sandy.",
                ),
                term_row(
                    "Total solids",
                    "everything except water",
                    "Fat, milk solids, sugars, fiber, egg solids, cocoa, stabilizers, and "
                    "other declared solids.",
                ),
                term_row(
                    "Fiber",
                    "declared dietary fiber",
                    "Counts toward total solids and may affect body and water mobility. The "
                    "effect depends on source, solubility, and particle size, so the calculator "
                    "does not turn fiber grams into a texture score.",
                ),
                class_="glossary-grid",
            ),
            ui.p(
                "POD and PAC conventions differ across calculators. This page reports the "
                "mix-normalized index used by its target ranges. Process, freezer temperature, "
                "ingredient labels, and evaporation still affect the finished texture.",
                class_="glossary-note",
            ),
            class_="glossary-section",
        ),
        class_="page-shell builder-page",
    )


def ingredient_page() -> ui.Tag:
    """Return the custom ingredient editor and seed library."""

    sugar_choices = {component: label for component, label in SOLUBLE_COMPONENT_LABELS.items()}
    return ui.div(
        page_intro(
            "Ingredients",
            "Match the product you actually use",
            "The built-in library is a starting point. Fruit ripeness and chocolate "
            "formulations vary, so use measured data or the product label when possible.",
        ),
        ui.div(
            ui.tags.section(
                ui.div("Fruit or purée", class_="eyebrow"),
                ui.h2("Describe the fruit"),
                ui.p(
                    "Water drives ice formation. The sucrose, glucose, and fructose split "
                    "changes both sweetness and freezing behavior. Fiber and other solids "
                    "add body, but their water binding and particle texture are not predicted."
                ),
                ui.input_text(
                    "fruit_name",
                    "Ingredient name",
                    placeholder="For example: ripe strawberry purée",
                    width="100%",
                ),
                ui.div(
                    ui.input_numeric(
                        "fruit_water", "Water · g", 90.8, min=0, max=100, step=0.01
                    ),
                    ui.input_numeric(
                        "fruit_sucrose", "Sucrose · g", 0, min=0, max=100, step=0.01
                    ),
                    ui.input_numeric(
                        "fruit_glucose", "Glucose · g", 2.24, min=0, max=100, step=0.01
                    ),
                    ui.input_numeric(
                        "fruit_fructose", "Fructose · g", 2.62, min=0, max=100, step=0.01
                    ),
                    ui.input_numeric(
                        "fruit_fiber", "Fiber · g", 0, min=0, max=100, step=0.01
                    ),
                    ui.input_numeric(
                        "fruit_fat", "Fat · g", 0.22, min=0, max=100, step=0.01
                    ),
                    ui.input_numeric(
                        "fruit_other", "Other solids · g", 4.12, min=0, max=100, step=0.01
                    ),
                    ui.input_numeric(
                        "fruit_brix", "Measured °Brix · optional", 0, min=0, max=100, step=0.1
                    ),
                    class_="guided-input-grid",
                ),
                ui.p(
                    "Reference values are USDA means for raw strawberries. Fiber is 0 only "
                    "because that record does not report it and is included in residual other "
                    "solids. °Brix is not substituted for the entered sugar composition.",
                    class_="field-note",
                ),
                ui.input_action_button(
                    "save_fruit",
                    ui.span(icon("plus"), "Add fruit or purée"),
                    class_="button button-primary",
                ),
                ui.output_ui("fruit_status"),
                class_="surface guided-ingredient-card fruit-card",
            ),
            ui.tags.section(
                ui.div("Chocolate or cocoa", class_="eyebrow"),
                ui.h2("Use the package label"),
                ui.p(
                    "Cocoa butter raises fat. Sugar changes POD and PAC. Cocoa solids, "
                    "protein, and fiber raise total solids and body. Particle size, cocoa "
                    "butter crystallization, and emulsification remain outside the model."
                ),
                ui.input_text(
                    "chocolate_name",
                    "Ingredient name",
                    placeholder="For example: 70% dark couverture",
                    width="100%",
                ),
                ui.div(
                    ui.input_numeric(
                        "chocolate_fat", "Fat · g", 0, min=0, max=100, step=0.1
                    ),
                    ui.input_numeric(
                        "chocolate_carbohydrate",
                        "Carbohydrate · g",
                        0,
                        min=0,
                        max=100,
                        step=0.1,
                    ),
                    ui.input_numeric(
                        "chocolate_sugars", "of which sugars · g", 0, min=0, max=100, step=0.1
                    ),
                    ui.input_numeric(
                        "chocolate_fiber", "Fiber · g", 0, min=0, max=100, step=0.1
                    ),
                    ui.input_numeric(
                        "chocolate_protein", "Protein · g", 0, min=0, max=100, step=0.1
                    ),
                    ui.input_numeric(
                        "chocolate_salt", "Salt · g", 0, min=0, max=100, step=0.01
                    ),
                    ui.input_numeric(
                        "chocolate_water", "Water · g", 0, min=0, max=100, step=0.1
                    ),
                    class_="guided-input-grid",
                ),
                ui.p(
                    "Leave water at 0 to infer it by difference. Label sugars are modeled "
                    "as sucrose. Use direct composition below if the manufacturer supplies "
                    "a more precise sugar or water analysis.",
                    class_="field-note",
                ),
                ui.input_action_button(
                    "save_chocolate",
                    ui.span(icon("plus"), "Add chocolate or cocoa"),
                    class_="button button-primary",
                ),
                ui.output_ui("chocolate_status"),
                class_="surface guided-ingredient-card chocolate-card",
            ),
            class_="guided-ingredient-grid",
        ),
        ui.tags.section(
            ui.div(
                ui.div("Other ingredient", class_="eyebrow"),
                ui.h2("Enter another product per 100 g"),
                ui.p(
                    "Use nutrition-label mode for ordinary products. Use direct composition "
                    "when you know the milk-solids, alcohol, gum, or sugar component."
                ),
                class_="section-heading-simple",
            ),
            ui.input_text(
                "custom_name",
                "Ingredient name",
                placeholder="For example: local 35% cream",
                width="100%",
            ),
            ui.input_radio_buttons(
                "custom_mode",
                "Entry method",
                choices={
                    "label": "Nutrition label",
                    "precision": "Direct composition",
                },
                selected="label",
                inline=True,
            ),
            ui.panel_conditional(
                "input.custom_mode === 'label'",
                ui.div(
                    ui.input_numeric("label_fat", "Fat · g", 0, min=0, max=100, step=0.1),
                    ui.input_numeric(
                        "label_carbohydrate",
                        "Carbohydrate · g",
                        0,
                        min=0,
                        max=100,
                        step=0.1,
                    ),
                    ui.input_numeric(
                        "label_sugars",
                        "of which sugars · g",
                        0,
                        min=0,
                        max=100,
                        step=0.1,
                    ),
                    ui.input_numeric(
                        "label_protein",
                        "Protein · g",
                        0,
                        min=0,
                        max=100,
                        step=0.1,
                    ),
                    ui.input_numeric("label_fibre", "Fibre · g", 0, min=0, max=100, step=0.1),
                    ui.input_numeric("label_salt", "Salt · g", 0, min=0, max=100, step=0.01),
                    ui.input_numeric("label_water", "Water · g", 0, min=0, max=100, step=0.1),
                    ui.input_select(
                        "label_sugar_type",
                        "Treat label sugars as",
                        choices=sugar_choices,
                        selected="sucrose",
                    ),
                    class_="custom-grid",
                ),
                ui.p(
                    "Leave water at 0 to infer it by difference. Label sugars default to sucrose.",
                    class_="field-note",
                ),
            ),
            ui.panel_conditional(
                "input.custom_mode === 'precision'",
                ui.div(
                    ui.input_numeric("direct_fat", "Fat · g", 0, min=0, max=100, step=0.1),
                    ui.input_numeric("direct_msnf", "MSNF · g", 0, min=0, max=100, step=0.1),
                    ui.input_select(
                        "direct_component",
                        "Soluble component",
                        choices=sugar_choices,
                        selected="sucrose",
                    ),
                    ui.input_numeric(
                        "direct_component_amount",
                        "Soluble component · g",
                        0,
                        min=0,
                        max=100,
                        step=0.1,
                    ),
                    ui.input_numeric(
                        "direct_fiber", "Fiber · g", 0, min=0, max=100, step=0.1
                    ),
                    ui.input_numeric(
                        "direct_other",
                        "Other solids · g",
                        0,
                        min=0,
                        max=100,
                        step=0.1,
                    ),
                    ui.input_numeric("direct_salt", "Salt · g", 0, min=0, max=100, step=0.01),
                    ui.input_numeric(
                        "direct_alcohol",
                        "Alcohol · g",
                        0,
                        min=0,
                        max=100,
                        step=0.1,
                    ),
                    ui.input_numeric("direct_gums", "Gums · g", 0, min=0, max=100, step=0.01),
                    ui.input_numeric("direct_water", "Water · g", 0, min=0, max=100, step=0.1),
                    class_="custom-grid",
                ),
                ui.p("Leave water at 0 to infer it by difference.", class_="field-note"),
            ),
            ui.div(
                ui.input_action_button(
                    "save_custom",
                    ui.span(icon("plus"), "Add to ingredient library"),
                    class_="button button-primary",
                ),
                ui.output_ui("custom_status"),
                class_="custom-actions",
            ),
            class_="surface custom-surface",
        ),
        ui.tags.section(
            ui.div(
                ui.div("Built-in data", class_="eyebrow"),
                ui.h2("Ingredient assumptions"),
                ui.p(
                    "Composition is shown per 100 g. POD/g and PAC/g are the modeled "
                    "contribution of one gram of ingredient."
                ),
                class_="section-heading-simple",
            ),
            ui.output_ui("ingredient_library"),
            class_="surface library-surface",
        ),
        class_="page-shell ingredient-page",
    )


def citations(*numbers: int) -> ui.Tag:
    """Return linked numeric superscript citations."""

    children: list[ui.Tag | str] = []
    for index, number in enumerate(numbers):
        if index:
            children.append(",")
        children.append(ui.tags.a(str(number), href=f"#ref-{number}"))
    return ui.tags.sup(*children, class_="citation")


def additive_row(
    name: str,
    role: str,
    hydration: str,
    guidance: ui.Tag,
) -> ui.Tag:
    """Create one additive guide row."""

    return ui.tags.tr(
        ui.tags.th(name, scope="row"),
        ui.tags.td(role),
        ui.tags.td(hydration),
        ui.tags.td(guidance),
    )


def reference_item(number: int, *children: ui.Tag | str) -> ui.Tag:
    """Create a numbered reference with an anchor target."""

    return ui.tags.li(*children, id=f"ref-{number}")


def additives_page() -> ui.Tag:
    """Return cited stabilizer, emulsifier, and additive guidance."""

    return ui.div(
        page_intro(
            "Formulation reference",
            "Stabilizers, emulsifiers, and other additives",
            "Use this page to choose a system, not to maximize the number of additives. "
            "Start low, weigh precisely, and change one part of the blend at a time.",
        ),
        ui.div(
            ui.div(
                ui.h2("Stabilizer and emulsifier are different jobs"),
                ui.p(
                    "Stabilizers manage the water phase. They change viscosity, melt, and the "
                    "growth of ice crystals during storage. Emulsifiers act mainly at fat "
                    "interfaces and help create the partially coalesced fat structure that "
                    "supports body, air cells, and controlled melting.",
                    citations(2, 6),
                ),
                ui.p(
                    "Most published evidence comes from churned ice cream. The same ingredient "
                    "functions are relevant to a CREAMi base, but the best dose may differ "
                    "because the machine processes a solid frozen tub with little incorporated air.",
                    class_="field-note",
                ),
            ),
            ui.div(
                ui.strong("Practical rule"),
                ui.p(
                    "For a full-fat dairy base, begin around 0.10% to 0.20% total stabilizer. "
                    "Higher is not automatically better. Excess gum can become chewy, elastic, "
                    "pasty, or slimy and can reduce air incorporation.",
                    citations(1, 3),
                ),
            ),
            class_="additive-intro",
        ),
        ui.tags.section(
            ui.div("Frequently useful systems", class_="eyebrow"),
            ui.h2("Combinations to start testing"),
            ui.div(
                ui.tags.article(
                    ui.div("Cold-process experiment", class_="system-tag"),
                    ui.h3("CMC + guar + lambda carrageenan"),
                    ui.p(
                        "A practical combination to test in a no-cook dairy base. CMC provides "
                        "ice-crystal control, guar adds body, and lambda carrageenan improves the "
                        "melted texture. All three can hydrate without the high heat required by LBG.",
                        citations(1, 3, 7),
                    ),
                    ui.tags.dl(
                        ui.tags.dt("Starting total"),
                        ui.tags.dd("0.15% to 0.20% of the mix"),
                        ui.tags.dt("Calculator default"),
                        ui.tags.dd("0.08% CMC + 0.06% guar + 0.04% lambda = 0.18%"),
                        ui.tags.dt("With no egg"),
                        ui.tags.dd("Add lecithin separately, often 0.15% to 0.30% to start"),
                    ),
                    ui.p(
                        "Underbelly's published 2:1:1 CMC–guar–lambda blend is a higher-dose "
                        "sorbet formula. The lower dairy dose above is an experimental adaptation, "
                        "not a research-derived dairy optimum. CMC can form gels with guar and "
                        "carrageenan, so reduce the total if the texture becomes elastic or pasty.",
                        citations(1),
                        class_="evidence-note",
                    ),
                    class_="system-card recommended-system",
                ),
                ui.tags.article(
                    ui.div("Cooked dairy", class_="system-tag"),
                    ui.h3("Locust bean gum + guar + lambda carrageenan"),
                    ui.p(
                        "A widely used general-purpose pattern. Underbelly suggests a 4:2:1 ratio "
                        "at about 0.15% of the total mix. Locust bean gum leads ice-crystal "
                        "control, guar strengthens body, and lambda carrageenan rounds the melt.",
                        citations(1, 2),
                    ),
                    ui.tags.dl(
                        ui.tags.dt("Starting blend per kg"),
                        ui.tags.dd("0.8 g LBG + 0.4 g guar + 0.2 g lambda"),
                        ui.tags.dt("Heat"),
                        ui.tags.dd("Required for LBG; verify the supplier's hydration temperature"),
                    ),
                    class_="system-card",
                ),
                ui.tags.article(
                    ui.div("Easy to source", class_="system-tag"),
                    ui.h3("Gelatin + xanthan"),
                    ui.p(
                        "Underbelly's accessible blend uses gelatin and xanthan at 3:1, about "
                        "0.15% total. Gelatin contributes a weak gel that melts in the mouth. "
                        "Xanthan supports the liquid melt but becomes slippery or slimy when overused.",
                        citations(1, 8),
                    ),
                    ui.tags.dl(
                        ui.tags.dt("Starting blend per kg"),
                        ui.tags.dd("1.0 g gelatin + 0.33 g xanthan"),
                        ui.tags.dt("Heat"),
                        ui.tags.dd("At least 60 °C to hydrate gelatin"),
                    ),
                    class_="system-card",
                ),
                ui.tags.article(
                    ui.div("Cold-process alternative", class_="system-tag"),
                    ui.h3("Guar + xanthan"),
                    ui.p(
                        "Both hydrate cold and are easy to buy. Published ice-cream work supports "
                        "xanthan as an effective stabilizer and has compared guar–xanthan blends "
                        "during long storage. Keep the total low because both strongly affect body.",
                        citations(3, 11),
                    ),
                    ui.tags.dl(
                        ui.tags.dt("Conservative trial"),
                        ui.tags.dd("0.05% guar + 0.05% xanthan"),
                        ui.tags.dt("Best for"),
                        ui.tags.dd("Small home trials where cold processing matters"),
                    ),
                    ui.p(
                        "The 1:1 trial is a practical starting point, not a single established optimum.",
                        class_="evidence-note",
                    ),
                    class_="system-card",
                ),
                class_="system-grid",
            ),
            class_="systems-section",
        ),
        ui.tags.section(
            ui.div("Individual ingredients", class_="eyebrow"),
            ui.h2("What each option contributes"),
            ui.div(
                ui.tags.table(
                    ui.tags.thead(
                        ui.tags.tr(
                            ui.tags.th("Ingredient"),
                            ui.tags.th("Main role"),
                            ui.tags.th("Hydration"),
                            ui.tags.th("Practical guidance"),
                        )
                    ),
                    ui.tags.tbody(
                        additive_row(
                            "CMC · cellulose gum",
                            "Crystal control, body",
                            "Cold",
                            ui.p(
                                "Very effective at suppressing ice-crystal growth. It can interact "
                                "strongly with guar and carrageenans, so use modest total doses.",
                                citations(1, 4, 7),
                            ),
                        ),
                        additive_row(
                            "Guar gum",
                            "Body, viscosity",
                            "Cold",
                            ui.p(
                                "Efficient and inexpensive. It supports CMC or LBG, but excess can "
                                "make the frozen texture chewy or elastic.",
                                citations(1, 4),
                            ),
                        ),
                        additive_row(
                            "Lambda carrageenan",
                            "Creamy melt, dairy-phase control",
                            "Cold",
                            ui.p(
                                "The non-gelling carrageenan usually preferred for a custard-like "
                                "melt. Keep it low and distinguish it from gelling kappa or iota types.",
                                citations(1),
                            ),
                        ),
                        additive_row(
                            "Locust bean gum · LBG",
                            "Crystal control, subtle body",
                            "Hot",
                            ui.p(
                                "A strong general-purpose ice-cream stabilizer. It pairs well with "
                                "guar and lambda carrageenan but requires adequate heat to hydrate.",
                                citations(1, 2),
                            ),
                        ),
                        additive_row(
                            "Xanthan gum",
                            "Viscosity, melt stability",
                            "Cold",
                            ui.p(
                                "Tolerates acid, alcohol, freezing, and thawing. It is convenient "
                                "but can become slippery or slimy and forms strong gels with LBG.",
                                citations(1, 3, 11),
                            ),
                        ),
                        additive_row(
                            "Gelatin",
                            "Weak gel, body, melt control",
                            "Hot",
                            ui.p(
                                "A traditional animal-protein stabilizer with a clean body-temperature "
                                "melt. It behaves differently from hydrolyzed collagen peptides.",
                                citations(1, 8),
                            ),
                        ),
                        additive_row(
                            "Collagen peptides",
                            "Protein solids; product-specific ice control",
                            "Usually cold",
                            ui.p(
                                "Do not treat ordinary collagen powder as a gram-for-gram gelatin "
                                "replacement. Specific bovine and fish gelatin hydrolysates inhibited "
                                "ice recrystallization in research systems, but activity depended on "
                                "peptide size and hydrolysis. No direct evidence establishes a "
                                "special collagen–xanthan combination.",
                                citations(9, 10),
                            ),
                        ),
                        additive_row(
                            "Tara gum",
                            "Body and water control",
                            "Warm to hot",
                            ui.p(
                                "A galactomannan option between guar and LBG in behavior. Treat the "
                                "supplier's hydration and dose guidance as authoritative.",
                                citations(1),
                            ),
                        ),
                        additive_row(
                            "Sodium alginate",
                            "Fluid gel, low-fat body",
                            "Cold; gels with calcium",
                            ui.p(
                                "Useful when a gel-like network is wanted, especially in lower-fat "
                                "bases. Dairy calcium can make it less forgiving than non-gelling gums.",
                                citations(1, 3),
                            ),
                        ),
                        additive_row(
                            "Kappa carrageenan",
                            "Strong dairy gel, whey control",
                            "Hot",
                            ui.p(
                                "Effective at very low concentration but can create a brittle gel. "
                                "It is not interchangeable with lambda carrageenan.",
                                citations(1, 3),
                            ),
                        ),
                    ),
                    class_="additive-table",
                ),
                class_="table-scroll",
            ),
            class_="additive-section",
        ),
        ui.tags.section(
            ui.div("Fat structure", class_="eyebrow"),
            ui.h2("Emulsifier options"),
            ui.div(
                ui.tags.article(
                    ui.h3("Soy or sunflower lecithin"),
                    ui.p(
                        "The most accessible egg-free option. Underbelly suggests 0.15% to 0.45% "
                        "per liter, with more sometimes needed in very high-fat mixes. Start near "
                        "0.15% to 0.30%. Too much can hinder whipping or add flavor.",
                        citations(5, 6),
                    ),
                ),
                ui.tags.article(
                    ui.h3("Egg yolk"),
                    ui.p(
                        "Provides lecithin, fat, protein, color, and custard flavor. Small amounts "
                        "can assist emulsification, while larger amounts also thicken and stabilize "
                        "the cooked base. High yolk levels can mute delicate flavors.",
                        citations(5),
                    ),
                ),
                ui.tags.article(
                    ui.h3("Mono- and diglycerides"),
                    ui.p(
                        "Commercially common and generally more effective than lecithin at promoting "
                        "partial fat coalescence. They are often paired with a small amount of "
                        "polysorbate 80.",
                        citations(6),
                    ),
                ),
                ui.tags.article(
                    ui.h3("Polysorbate 80"),
                    ui.p(
                        "Very effective at low dose and frequently blended with mono- and "
                        "diglycerides. It requires accurate weighing and is mainly useful when "
                        "churned foam structure and melt resistance are priorities.",
                        citations(6),
                    ),
                ),
                class_="emulsifier-grid",
            ),
            class_="additive-section",
        ),
        ui.tags.section(
            ui.div("Method", class_="eyebrow"),
            ui.h2("How to test a blend"),
            ui.tags.ol(
                process_step(
                    "1",
                    "Work in percentages",
                    "For a 709 g batch, 0.10% is 0.709 g. Use a scale readable to 0.01 g.",
                ),
                process_step(
                    "2",
                    "Disperse before hydrating",
                    "Mix gums thoroughly into at least ten times their weight in sugar or another "
                    "dry ingredient, then add gradually while blending.",
                ),
                process_step(
                    "3",
                    "Respect the hydration requirement",
                    "Cold-soluble does not mean instant. Heat LBG, gelatin, and gelling carrageenans "
                    "as required by the supplier. Age the base after hydration.",
                ),
                process_step(
                    "4",
                    "Change one variable at a time",
                    "Hold recipe, freezer temperature, aging time, and processing constant. Adjust "
                    "the total stabilizer in small steps of about 0.02 percentage points.",
                ),
                class_="method-list testing-list",
            ),
            class_="additive-section",
        ),
        ui.tags.section(
            ui.div("References", class_="eyebrow"),
            ui.h2("Evidence behind this guide"),
            ui.tags.ol(
                reference_item(
                    1,
                    "Underbelly. ",
                    ui.tags.a(
                        "Ice Cream Stabilizers",
                        href="https://under-belly.org/ice-cream-stabilizers/",
                        target="_blank",
                    ),
                    ". Practical hydrocolloid functions, blends, hydration, and dose guidance.",
                ),
                reference_item(
                    2,
                    "Caldwell KB, Goff HD, Stanley DW. ",
                    ui.tags.a(
                        "A Low-Temperature Scanning Electron Microscopy Study of Ice Cream. II",
                        href=("https://digitalcommons.usu.edu/foodmicrostructure/vol11/iss1/2/"),
                        target="_blank",
                    ),
                    ". Food Structure. 1992;11(1).",
                ),
                reference_item(
                    3,
                    "Soukoulis C, Chandrinos I, Tzia C. ",
                    ui.tags.a(
                        "Study of selected hydrocolloids and κ-carrageenan in ice cream",
                        href="https://doi.org/10.1016/j.lwt.2007.12.009",
                        target="_blank",
                    ),
                    ". LWT. 2008;41:1816-1827.",
                ),
                reference_item(
                    4,
                    "BahramParvar M, et al. ",
                    ui.tags.a(
                        "Optimization of stabilizer combinations for ice cream",
                        href="https://doi.org/10.1007/s13197-013-1133-5",
                        target="_blank",
                    ),
                    ". J Food Sci Technol. 2015;52:1480-1488.",
                ),
                reference_item(
                    5,
                    "Underbelly. ",
                    ui.tags.a(
                        "Ice Cream Emulsifiers",
                        href="https://under-belly.org/ice-cream-emulsifiers/",
                        target="_blank",
                    ),
                    ". Practical lecithin, egg-yolk, and commercial emulsifier guidance.",
                ),
                reference_item(
                    6,
                    "Baer RJ, Wolkow MD, Kasperson KM. ",
                    ui.tags.a(
                        "Effect of Emulsifiers on the Body and Texture of Low Fat Ice Cream",
                        href="https://doi.org/10.3168/jds.S0022-0302(97)76283-0",
                        target="_blank",
                    ),
                    ". J Dairy Sci. 1997;80:3123-3132.",
                ),
                reference_item(
                    7,
                    "Cheng J, Ma Y, Li X, Yan T, Cui J. ",
                    ui.tags.a(
                        "Effects of milk protein-polysaccharide interactions on the stability "
                        "of ice cream mix model systems",
                        href="https://doi.org/10.1016/j.foodhyd.2014.11.027",
                        target="_blank",
                    ),
                    ". Food Hydrocolloids. 2015;45:327-336.",
                ),
                reference_item(
                    8,
                    "Milliatti MC, Lannes SCS. ",
                    ui.tags.a(
                        "Impact of stabilizers on the rheological properties of ice creams",
                        href="https://doi.org/10.1590/fst.31818",
                        target="_blank",
                    ),
                    ". Food Sci Technol. 2018;38:733-739.",
                ),
                reference_item(
                    9,
                    "Wang SY, Damodaran S. ",
                    ui.tags.a(
                        "Ice-structuring peptides derived from bovine collagen",
                        href="https://doi.org/10.1021/jf900524y",
                        target="_blank",
                    ),
                    ". J Agric Food Chem. 2009;57:5501-5509.",
                ),
                reference_item(
                    10,
                    "Damodaran S, Wang S. ",
                    ui.tags.a(
                        "Ice crystal growth inhibition by fish gelatin hydrolysate peptides",
                        href="https://doi.org/10.1016/j.foodhyd.2017.03.029",
                        target="_blank",
                    ),
                    ". Food Hydrocolloids. 2017;70:46-56.",
                ),
                reference_item(
                    11,
                    "Klesment T, Stekolštšikova J, Laos K. ",
                    ui.tags.a(
                        "The influence of hydrocolloids on storage quality of 10% dairy fat ice cream",
                        href=(
                            "https://ws.lib.ttu.ee/publikatsioonid/en/Publ/Item/"
                            "0bca5149-46c5-4a8a-97a5-2de7f08d9354"
                        ),
                        target="_blank",
                    ),
                    ". Agronomy Research. 2011;9(S2):403-408.",
                ),
                class_="reference-list",
            ),
            class_="additive-section references-section",
        ),
        class_="page-shell additives-page",
    )


def process_step(number: str, title: str, text: str) -> ui.Tag:
    """Create one process step."""

    return ui.tags.li(
        ui.span(number, class_="method-number"),
        ui.div(ui.h3(title), ui.p(text)),
    )


def method_page() -> ui.Tag:
    """Return process guidance and model notes."""

    return ui.div(
        page_intro(
            "Process notes",
            "Use the method that matches the base",
            "The calculator balances ingredient composition. Heating, cooling, aging, "
            "freezing, and evaporation still change the result.",
        ),
        ui.div(
            ui.tags.aside(
                ui.strong("On this page"),
                ui.tags.a("No-cook base", href="#no-cook"),
                ui.tags.a("Cooked egg-free base", href="#cooked"),
                ui.tags.a("Egg custard", href="#custard"),
                ui.tags.a("Fruit sorbet", href="#sorbet"),
                ui.tags.a("CREAMi processing", href="#creami"),
                ui.tags.a("Sources", href="#sources"),
                class_="method-toc",
            ),
            ui.tags.main(
                ui.tags.section(
                    ui.div("Cold process", class_="eyebrow"),
                    ui.h2("No-cook dairy base", id="no-cook"),
                    ui.tags.ol(
                        process_step(
                            "1",
                            "Mix the powders first",
                            "Combine milk powder, sugars, salt, and cold-dispersible stabilizers "
                            "before they meet liquid. This reduces clumping.",
                        ),
                        process_step(
                            "2",
                            "Blend into cold dairy",
                            "Add the powder blend gradually while mixing. Stop when smooth so the "
                            "cream does not begin to churn into butter.",
                        ),
                        process_step(
                            "3",
                            "Age under refrigeration",
                            "Chill below 4 °C for 12 to 24 hours so the solids hydrate and the fat "
                            "crystallizes.",
                        ),
                        process_step(
                            "4",
                            "Weigh, fill, and freeze",
                            "Stir briefly, weigh the finished mix, and keep the tub below its MAX "
                            "line. Freeze level for at least 24 hours.",
                        ),
                        class_="method-list",
                    ),
                    class_="method-section",
                ),
                ui.tags.section(
                    ui.div("Dairy-free base", class_="eyebrow"),
                    ui.h2("Fruit sorbet", id="sorbet"),
                    ui.p(
                        "Fruit sorbet is balanced around water, total solids, individual "
                        "sugars, POD, and PAC. Fat is measured rather than targeted, and MSNF "
                        "does not apply. The experimental profile is a starting guide because "
                        "fruit, acidity, freezer temperature, and machine behavior all vary."
                    ),
                    ui.tags.ol(
                        process_step(
                            "1",
                            "Check the fruit",
                            "Use the composition of the actual purée when available. A measured "
                            "Brix helps identify a sweeter or more dilute batch, but it does not "
                            "replace water and sugar-species data.",
                        ),
                        process_step(
                            "2",
                            "Disperse and blend",
                            "Mix the dry sugars, inulin, salt, and stabilizers before blending "
                            "them into the fruit and water. Follow each stabilizer's hydration "
                            "requirements.",
                        ),
                        process_step(
                            "3",
                            "Rest cold",
                            "Chill the mix and allow the stabilizers to hydrate. Recheck the "
                            "batch mass if heating or straining removed water or pulp.",
                        ),
                        process_step(
                            "4",
                            "Freeze, test, and record",
                            "Use the selected machine, record the freezer temperature and fruit "
                            "Brix, then adjust one variable at a time in the next batch.",
                        ),
                        class_="method-list",
                    ),
                    ui.div(
                        icon("info"),
                        ui.p(
                            "Fiber is included in total solids, but the app does not predict "
                            "water binding, viscosity, particle texture, or organic-acid PAC. "
                            "Treat the optimized result as a starting point and verify it in a "
                            "small test batch."
                        ),
                        class_="callout",
                    ),
                    class_="method-section",
                ),
                ui.tags.section(
                    ui.div("Heated process", class_="eyebrow"),
                    ui.h2("Cooked dairy base without egg", id="cooked"),
                    ui.p(
                        "Heat activates locust bean gum and supports dairy-protein hydration. "
                        "Use a thermometer, stir continuously, and avoid prolonged boiling."
                    ),
                    ui.tags.ol(
                        process_step(
                            "1",
                            "Combine liquid and dry ingredients",
                            "Disperse stabilizers through the bulk sugars before whisking them into "
                            "milk and cream.",
                        ),
                        process_step(
                            "2",
                            "Heat the complete mix",
                            "Follow the time and temperature appropriate to your stabilizer system "
                            "and food-safety setting. Do not rely on visual simmering alone.",
                        ),
                        process_step(
                            "3",
                            "Restore the intended batch mass",
                            "Cooking removes water. Weigh the mix after heating and add milk or water "
                            "to return to the calculated mass if you want the displayed composition.",
                        ),
                        process_step(
                            "4",
                            "Cool quickly and age",
                            "Use an ice bath or another rapid-cooling method, then refrigerate before "
                            "freezing.",
                        ),
                        class_="method-list",
                    ),
                    class_="method-section",
                ),
                ui.tags.section(
                    ui.div("Egg bases", class_="eyebrow"),
                    ui.h2("Yolk or whole-egg custard", id="custard"),
                    ui.div(
                        ui.div(
                            ui.strong("Egg yolks"),
                            ui.p(
                                "Add fat, proteins, color, flavor, and phospholipid emulsifiers. "
                                "The starting formula uses 5% yolk."
                            ),
                        ),
                        ui.div(
                            ui.strong("Whole eggs"),
                            ui.p(
                                "Add more water and protein per gram than yolks. The starting formula "
                                "uses 8% whole egg."
                            ),
                        ),
                        class_="comparison-grid",
                    ),
                    ui.tags.ol(
                        process_step(
                            "1",
                            "Whisk eggs with part of the sugar",
                            "This distributes the egg and slows local protein coagulation.",
                        ),
                        process_step(
                            "2",
                            "Temper with the hot dairy",
                            "Add hot dairy gradually while whisking, then return the mixture to the pan.",
                        ),
                        process_step(
                            "3",
                            "Cook with temperature control",
                            "Stir continuously and use a validated egg-custard process. Raw or "
                            "undercooked egg mixtures carry a food-safety risk.",
                        ),
                        process_step(
                            "4",
                            "Strain, restore mass, and cool quickly",
                            "Strain out any coagulated egg, correct for evaporated water by weight, "
                            "then chill promptly before aging.",
                        ),
                        class_="method-list",
                    ),
                    ui.div(
                        icon("info"),
                        ui.p(
                            "The ingredient model includes egg composition but does not model "
                            "protein coagulation, pasteurization, or water lost during cooking."
                        ),
                        class_="callout",
                    ),
                    class_="method-section",
                ),
                ui.tags.section(
                    ui.div("Frozen processing", class_="eyebrow"),
                    ui.h2("CREAMi and Pacojet batches", id="creami"),
                    ui.p(
                        "The default PAC target is higher than the churned target because a "
                        "CREAMi-style machine processes a fully frozen container. Freeze the tub "
                        "level, keep below MAX FILL, and use the program appropriate to the recipe."
                    ),
                    ui.div(
                        ui.div(
                            ui.span("Churned machine", class_="comparison-label"),
                            ui.strong("PAC 220 to 230"),
                            ui.p("A starting range for extraction at a warmer draw temperature."),
                        ),
                        ui.div(
                            ui.span("CREAMi or Pacojet", class_="comparison-label"),
                            ui.strong("PAC 245 to 255"),
                            ui.p("A starting range for processing a hard-frozen batch."),
                        ),
                        class_="comparison-grid",
                    ),
                    class_="method-section",
                ),
                ui.tags.section(
                    ui.div("References", class_="eyebrow"),
                    ui.h2("Sources and conventions", id="sources"),
                    ui.tags.ul(
                        ui.tags.li(
                            ui.tags.a(
                                "Underbelly: Sugars in Ice Cream",
                                href="https://under-belly.org/sugars-in-ice-cream/",
                                target="_blank",
                            )
                        ),
                        ui.tags.li(
                            ui.tags.a(
                                "Underbelly: Ice Cream Stabilizers",
                                href="https://under-belly.org/ice-cream-stabilizers/",
                                target="_blank",
                            )
                        ),
                        ui.tags.li(
                            ui.tags.a(
                                "Ice Cream Science: Why are emulsifiers used in ice cream?",
                                href="https://www.icecreamscience.com/blog/why-are-emulsifiers-used-in-ice-cream",
                                target="_blank",
                            )
                        ),
                        ui.tags.li(
                            ui.tags.a(
                                "Ninja CREAMi Deluxe owner guidance",
                                href=(
                                    "https://support.ninjakitchen.co.uk/hc/en-gb/sections/"
                                    "12373335215644-NC501UK-Series"
                                ),
                                target="_blank",
                            )
                        ),
                        ui.tags.li(
                            ui.tags.a(
                                "USDA FoodData Central: Foundation Foods",
                                href="https://fdc.nal.usda.gov/Foundation_Foods_Documentation/",
                                target="_blank",
                            )
                        ),
                        ui.tags.li(
                            ui.tags.a(
                                "Underbelly: Sample Sorbet Recipe · Strawberry",
                                href="https://under-belly.org/sample-sorbet-recipe/",
                                target="_blank",
                            )
                        ),
                        ui.tags.li(
                            ui.tags.a(
                                "Research note: sorbet, fruit, and chocolate formulation",
                                href=(
                                    f"{REPOSITORY_URL}/blob/main/research/"
                                    "sorbet_and_complex_ingredients.md"
                                ),
                                target="_blank",
                            )
                        ),
                        class_="source-list",
                    ),
                    ui.p(
                        "Ingredient composition and PAC/POD coefficients are model assumptions. "
                        "Check package labels and keep notes from actual batches.",
                        class_="field-note",
                    ),
                    class_="method-section",
                ),
                class_="method-content",
            ),
            class_="method-layout",
        ),
        class_="page-shell method-page",
    )


app_ui = ui.page_navbar(
    ui.head_content(
        ui.tags.meta(name="viewport", content="width=device-width, initial-scale=1"),
        ui.tags.link(rel="preconnect", href="https://fonts.googleapis.com"),
        ui.tags.link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin="anonymous"),
        ui.tags.link(
            rel="stylesheet",
            href=(
                "https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:"
                "wght@400;500;600;700;800&family=DM+Mono:wght@400;500&"
                "family=Nunito+Sans:wght@400;500;600;700;800&display=swap"
            ),
        ),
        ui.include_js(APP_DIR / "app.js", method="inline"),
        ui.include_css(APP_DIR / "styles.css"),
    ),
    ui.nav_panel("Overview", landing_page(), value="start"),
    ui.nav_panel("Calculator", builder_page(), value="builder"),
    ui.nav_panel("Ingredients", ingredient_page(), value="ingredients"),
    ui.nav_panel("Stabilizers & additives", additives_page(), value="additives"),
    ui.nav_panel("Process notes", method_page(), value="method"),
    ui.nav_spacer(),
    ui.nav_control(
        ui.tags.a(
            "GitHub",
            href=REPOSITORY_URL,
            target="_blank",
            rel="noopener noreferrer",
            class_="nav-project-link",
        )
    ),
    ui.nav_control(
        ui.div(
            ui.span("Theme", class_="visually-hidden"),
            ui.input_dark_mode(id="dark_mode"),
            class_="theme-control",
        )
    ),
    title=ui.div(
        ui.span("Ice Cream", ui.tags.br(), "Formula Calculator", class_="brand-title"),
        ui.tags.small(f"v{APP_VERSION}"),
        class_="brand",
    ),
    id="main_nav",
    selected="start",
    window_title="Ice Cream Formula Calculator",
    fluid=True,
    footer=app_footer(),
    navbar_options=ui.navbar_options(position="static-top", collapsible=True),
)


def server(input: Inputs, output: Outputs, session: Session) -> None:
    """Run one independent formulation session."""

    recipe_state = reactive.Value(scale_recipe(base_recipe("no_cook"), BATCH_MASSES["deluxe"]))
    library_state = reactive.Value(default_library())
    solver_message = reactive.Value(
        ("info", "The standard dairy and sugar rows are selected for auto-adjustment.")
    )
    custom_message = reactive.Value(
        (
            "info",
            (
                "Added ingredients are available until this page is reloaded. "
                "Shinylive does not persist them yet."
            ),
        )
    )
    fruit_message = reactive.Value(
        ("info", "Use a food database, supplier analysis, or measurements from the actual fruit.")
    )
    chocolate_message = reactive.Value(
        ("info", "Package values are preferable because cocoa products vary substantially.")
    )
    custom_counter = reactive.Value(1)

    def selected_batch_mass() -> float:
        """Return the requested working mass for the batch-size control."""

        choice = str(input.batch_size() or "deluxe")
        if choice == "custom":
            value = float(input.custom_batch_mass() or 0)
        elif choice in BATCH_MASSES:
            value = BATCH_MASSES[choice]
        else:
            expected = ", ".join([*BATCH_MASSES, "custom"])
            raise ValueError(f"Unknown batch size {choice!r}; expected one of: {expected}.")
        if value <= 0:
            raise ValueError(f"Batch mass must be positive; got {value!r}.")
        return value

    def current_lines() -> list[RecipeLine]:
        """Read current dynamic row inputs, falling back to stored values."""

        stored = recipe_state.get()
        current: list[RecipeLine] = []
        for index, line in enumerate(stored):
            ingredient_value = input[f"ingredient_{index}"]()
            gram_value = input[f"grams_{index}"]()
            free_value = input[f"free_{index}"]()
            current.append(
                RecipeLine(
                    ingredient_id=str(ingredient_value or line.ingredient_id),
                    grams=float(line.grams if gram_value is None else gram_value),
                    free=bool(line.free if free_value is None else free_value),
                )
            )
        return current

    @reactive.calc
    def live_lines() -> list[RecipeLine]:
        return current_lines()

    @reactive.calc
    def live_metrics():
        return calculate_recipe(live_lines(), library_state.get())

    @reactive.effect
    def _initialize_add_choices() -> None:
        ui.update_selectize(
            "add_ingredient",
            choices=ingredient_choices(library_state.get()),
            selected="whole_milk_35",
            session=session,
        )

    @reactive.effect
    @reactive.event(input.start_building)
    def _start_building() -> None:
        ui.update_navset("main_nav", selected="builder", session=session)

    @reactive.effect
    @reactive.event(input.open_method)
    def _open_method() -> None:
        ui.update_navset("main_nav", selected="method", session=session)

    @reactive.effect
    @reactive.event(input.target_profile)
    def _apply_profile_defaults() -> None:
        profile = str(input.target_profile() or "Creami / Pacojet")
        if profile == "Fruit sorbet · experimental":
            ui.update_slider("target_solids", value=29.0, session=session)
            ui.update_slider("target_pod", value=170, session=session)
            ui.update_slider("target_pac", value=320, session=session)
        elif profile == "Churned machine":
            ui.update_slider("target_fat", value=13.5, session=session)
            ui.update_numeric("target_msnf", value=11.5, session=session)
            ui.update_slider("target_pod", value=112, session=session)
            ui.update_slider("target_pac", value=225, session=session)
        else:
            ui.update_slider("target_fat", value=13.5, session=session)
            ui.update_numeric("target_msnf", value=11.5, session=session)
            ui.update_slider("target_pod", value=112, session=session)
            ui.update_slider("target_pac", value=248, session=session)

    @render.ui
    def base_summary():
        preset_id = str(input.base_style() or "no_cook")
        info = BASE_PRESET_INFO.get(preset_id, BASE_PRESET_INFO["no_cook"])
        return ui.div(
            ui.strong(info["name"]),
            ui.span(info["description"]),
            ui.tags.small(info["process"]),
            class_="base-summary",
        )

    @render.ui
    def formula_table():
        lines = recipe_state.get()
        library = library_state.get()
        choices = ingredient_choices(library)
        rows: list[ui.Tag] = []
        for index, line in enumerate(lines):
            ingredient = library[line.ingredient_id]
            rows.append(
                ui.tags.tr(
                    ui.tags.td(
                        ui.span(f"{index + 1:02d}", class_="row-index"),
                        **{"data-label": "Row"},
                    ),
                    ui.tags.td(
                        ui.input_selectize(
                            f"ingredient_{index}",
                            None,
                            choices=choices,
                            selected=line.ingredient_id,
                            width="100%",
                            options={"placeholder": "Choose an ingredient"},
                        ),
                        **{"data-label": "Ingredient"},
                    ),
                    ui.tags.td(
                        ui.input_numeric(
                            f"grams_{index}",
                            None,
                            value=round(line.grams, 2),
                            min=0,
                            max=5000,
                            step=0.01,
                            width="100%",
                            update_on="blur",
                        ),
                        **{"data-label": "Quantity · g"},
                    ),
                    ui.tags.td(
                        ui.input_checkbox(
                            f"free_{index}",
                            "Allow",
                            value=line.free,
                        ),
                        **{"data-label": "Auto-adjust"},
                    ),
                    ui.tags.td(
                        ui.input_action_link(
                            f"remove_{index}",
                            icon("trash"),
                            class_="row-remove",
                            title=f"Remove {ingredient.name}",
                            **{"aria-label": f"Remove {ingredient.name}"},
                        ),
                        **{"data-label": "Remove"},
                    ),
                )
            )
        return ui.tags.table(
            ui.tags.thead(
                ui.tags.tr(
                    ui.tags.th("#"),
                    ui.tags.th("Ingredient"),
                    ui.tags.th("Quantity · g"),
                    ui.tags.th(
                        "Auto-adjust",
                        ui.tags.span(
                            "?",
                            class_="help-dot",
                            title="The optional optimizer may change rows marked Allow.",
                        ),
                    ),
                    ui.tags.th(ui.tags.span("Remove", class_="visually-hidden")),
                )
            ),
            ui.tags.tbody(*rows),
            class_="formula-table",
        )

    def register_remove_handler(row_index: int) -> reactive.Effect_:
        @reactive.effect
        @reactive.event(input[f"remove_{row_index}"])
        def _remove_row() -> None:
            lines = current_lines()
            if row_index >= len(lines):
                return
            if len(lines) == 1:
                ui.notification_show(
                    "A recipe needs at least one row.",
                    type="warning",
                    session=session,
                )
                return
            removed = library_state.get()[lines[row_index].ingredient_id].name
            recipe_state.set(lines[:row_index] + lines[row_index + 1 :])
            ui.notification_show(
                f"Removed {removed}.",
                type="message",
                duration=2,
                session=session,
            )

        return _remove_row

    _remove_handlers = [register_remove_handler(row_index) for row_index in range(MAX_RECIPE_ROWS)]

    @reactive.effect
    @reactive.event(input.add_line)
    def _add_line() -> None:
        lines = current_lines()
        if len(lines) >= MAX_RECIPE_ROWS:
            ui.notification_show(
                f"The recipe is limited to {MAX_RECIPE_ROWS} rows.",
                type="warning",
                session=session,
            )
            return
        ingredient_id = str(input.add_ingredient() or "whole_milk_35")
        grams = float(input.add_grams() or 0)
        recipe_state.set(lines + [RecipeLine(ingredient_id, grams, False)])
        ui.notification_show(
            f"Added {library_state.get()[ingredient_id].name}.",
            type="message",
            duration=2,
            session=session,
        )

    @reactive.effect
    @reactive.event(input.load_base)
    def _load_base() -> None:
        preset_id = str(input.base_style() or "no_cook")
        try:
            loaded = scale_recipe(base_recipe(preset_id), selected_batch_mass())
        except ValueError as exc:
            ui.notification_show(str(exc), type="error", session=session)
            return
        recipe_state.set(loaded)
        metrics = calculate_recipe(loaded, library_state.get())
        current_profile = str(input.target_profile() or "Creami / Pacojet")
        if preset_id == "strawberry_sorbet":
            selected_profile = "Fruit sorbet · experimental"
        elif current_profile == "Fruit sorbet · experimental":
            selected_profile = "Creami / Pacojet"
        else:
            selected_profile = current_profile
        ui.update_select(
            "target_profile",
            selected=selected_profile,
            session=session,
        )
        ui.update_slider("target_fat", value=round(metrics.fat_pct, 1), session=session)
        ui.update_slider("target_pod", value=round(metrics.pod), session=session)
        ui.update_slider("target_pac", value=round(metrics.pac), session=session)
        ui.update_slider(
            "target_solids",
            value=round(metrics.total_solids_pct * 2) / 2,
            session=session,
        )
        ui.update_numeric("target_msnf", value=round(metrics.msnf_pct, 1), session=session)
        if preset_id == "strawberry_sorbet":
            solver_message.set(
                (
                    "info",
                    "Sorbet loaded. Fruit, water, and three sugars are ready for optimization.",
                )
            )
        else:
            solver_message.set(
                ("info", "Base loaded. The standard rows are available for auto-adjustment.")
            )
        ui.notification_show(
            f"Loaded {BASE_PRESET_INFO[preset_id]['name']} at {metrics.total_mass:.0f} g.",
            type="message",
            duration=3,
            session=session,
        )

    @reactive.effect
    @reactive.event(input.resize_recipe)
    def _resize_recipe() -> None:
        try:
            target_mass = selected_batch_mass()
            scaled = scale_recipe(current_lines(), target_mass)
        except ValueError as exc:
            ui.notification_show(str(exc), type="error", session=session)
            return
        recipe_state.set(scaled)
        ui.notification_show(
            f"Resized the current recipe to {target_mass:.0f} g.",
            type="message",
            duration=3,
            session=session,
        )

    @reactive.effect
    @reactive.event(input.solve_formula)
    def _solve_formula() -> None:
        is_sorbet = input.target_profile() == "Fruit sorbet · experimental"
        try:
            result = optimize_recipe(
                current_lines(),
                library_state.get(),
                Targets(
                    total_mass=selected_batch_mass(),
                    fat_pct=(
                        float(input.target_fat() or 0)
                        if not is_sorbet and input.optimize_fat()
                        else None
                    ),
                    msnf_pct=(
                        float(input.target_msnf() or 0)
                        if not is_sorbet and input.optimize_msnf()
                        else None
                    ),
                    total_solids_pct=(
                        float(input.target_solids() or 0) if input.optimize_solids() else None
                    ),
                    pod=float(input.target_pod() or 0) if input.optimize_pod() else None,
                    pac=float(input.target_pac() or 0) if input.optimize_pac() else None,
                ),
            )
        except (FormulationError, ValueError) as exc:
            solver_message.set(("error", str(exc)))
            return
        recipe_state.set(result.lines)
        labels = {
            "fat_pct": ("fat", " percentage points"),
            "msnf_pct": ("milk solids-not-fat", " percentage points"),
            "total_solids_pct": ("total solids", " percentage points"),
            "pod": ("POD", ""),
            "pac": ("PAC", ""),
        }
        exact_limits = {
            "fat_pct": 0.05,
            "msnf_pct": 0.05,
            "total_solids_pct": 0.05,
            "pod": 0.5,
            "pac": 0.5,
        }
        remaining = [
            f"{labels[name][0]} {error:+.1f}{labels[name][1]}"
            for name, error in result.target_errors.items()
            if abs(error) > exact_limits[name]
        ]
        if remaining:
            solver_message.set(
                (
                    "info",
                    "Closest fit found. Remaining target gaps: " + ", ".join(remaining) + ".",
                )
            )
        else:
            solver_message.set(
                (
                    "success",
                    (
                        f"Optimized {sum(line.free for line in result.lines)} selected "
                        f"ingredient rows across {len(result.target_errors)} targets."
                    ),
                )
            )

    @render.ui
    def solver_status():
        level, message = solver_message.get()
        return ui.div(message, class_=f"inline-status inline-status-{level}")

    @render.ui
    def results_panel():
        metrics = live_metrics()
        profile = str(input.target_profile() or "Creami / Pacojet")
        is_sorbet = profile == "Fruit sorbet · experimental"
        fat_target = float(input.target_fat() or 13.5)
        solids_target = float(input.target_solids() or 29.0)
        pod_target = float(input.target_pod() or 112)
        pac_target = float(input.target_pac() or 248)
        ranges = target_ranges(profile, fat_cap=18.0)
        if is_sorbet:
            ranges["total_solids_pct"] = (
                max(0.0, solids_target - 2.0),
                solids_target + 2.0,
            )
        else:
            ranges["fat_pct"] = (max(0.0, fat_target - 1.0), fat_target + 1.0)
        ranges["pod"] = (pod_target - 5.0, pod_target + 5.0)
        ranges["pac"] = (pac_target - 5.0, pac_target + 5.0)

        target_notes: list[str] = []
        if not is_sorbet and abs(metrics.fat_pct - fat_target) > 1.0:
            direction = "above" if metrics.fat_pct > fat_target else "below"
            target_notes.append(
                f"Fat is {abs(metrics.fat_pct - fat_target):.1f} percentage points "
                f"{direction} your target."
            )
        if is_sorbet and abs(metrics.total_solids_pct - solids_target) > 2.0:
            direction = "above" if metrics.total_solids_pct > solids_target else "below"
            target_notes.append(
                f"Total solids are {abs(metrics.total_solids_pct - solids_target):.1f} "
                f"percentage points {direction} your target."
            )
        if abs(metrics.pod - pod_target) > 5.0:
            direction = "sweeter than" if metrics.pod > pod_target else "less sweet than"
            target_notes.append(
                f"Sweetness is {abs(metrics.pod - pod_target):.0f} POD {direction} your target."
            )
        if abs(metrics.pac - pac_target) > 5.0:
            direction = "softer" if metrics.pac > pac_target else "harder"
            target_notes.append(
                f"Freeze softness is {abs(metrics.pac - pac_target):.0f} PAC from target "
                f"and is likely to run {direction}."
            )
        warnings = [
            *target_notes,
            *diagnose_recipe(metrics, fat_cap=18.0, target_set=profile),
        ]

        def balance_card(
            label: str,
            value: float,
            target: float,
            unit: str,
            scale_min: float,
            scale_max: float,
            digits: int,
        ) -> ui.Tag:
            current_position = min(
                100.0,
                max(0.0, 100.0 * (value - scale_min) / (scale_max - scale_min)),
            )
            target_position = min(
                100.0,
                max(0.0, 100.0 * (target - scale_min) / (scale_max - scale_min)),
            )
            return ui.div(
                ui.div(
                    ui.span(label),
                    ui.strong(f"{value:.{digits}f}{unit}"),
                    class_="balance-card-head",
                ),
                ui.div(
                    ui.span(class_="balance-fill", style=f"width:{current_position:.2f}%"),
                    ui.tags.i(class_="balance-target", style=f"left:{target_position:.2f}%"),
                    class_="balance-track",
                ),
                ui.tags.small(f"Target {target:.{digits}f}{unit}"),
                class_="balance-card",
            )

        metric_specs = [
            ("Fat", "fat_pct", metrics.fat_pct, "%", 2),
            ("MSNF", "msnf_pct", metrics.msnf_pct, "%", 2),
            (
                "Modeled sugars",
                "modeled_sugars_pct",
                metrics.modeled_sugars_pct,
                "%",
                2,
            ),
            ("Nonfat solids", "nonfat_solids_pct", metrics.nonfat_solids_pct, "%", 2),
            ("Total solids", "total_solids_pct", metrics.total_solids_pct, "%", 2),
            ("Water", "water_pct", metrics.water_pct, "%", 2),
            ("Fiber", "fiber_pct", metrics.fiber_pct, "%", 2),
            ("Gums", "gums_pct", metrics.gums_pct, "%", 3),
            ("Sweetness · POD", "pod", metrics.pod, "", 1),
            ("Freeze softness · PAC", "pac", metrics.pac, "", 1),
        ]
        metric_rows = []
        for label, key, value, suffix, digits in metric_specs:
            guide = ranges[key]
            if guide is None:
                target_text = "N/A" if is_sorbet and key == "msnf_pct" else "Measured"
                status = target_text
                status_class = "status-info"
            else:
                low, high = guide
                target_text = f"{low:g} to {high:g}{suffix}"
                status = "In range" if low <= value <= high else "Review"
                status_class = "status-ok" if status == "In range" else "status-review"
            metric_rows.append(
                ui.tags.tr(
                    ui.tags.th(label, scope="row"),
                    ui.tags.td(f"{value:.{digits}f}{suffix}", class_="numeric"),
                    ui.tags.td(target_text, class_="numeric target-value"),
                    ui.tags.td(ui.span(status, class_=f"status-pill {status_class}")),
                )
            )

        sugar_total = sum(metrics.sugar_grams.values())
        sugar_rows = []
        for component, grams in sorted(
            metrics.sugar_grams.items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            share = 100 * grams / sugar_total if sugar_total else 0
            sugar_rows.append(
                ui.tags.tr(
                    ui.tags.th(SOLUBLE_COMPONENT_LABELS.get(component, component), scope="row"),
                    ui.tags.td(f"{grams:.1f} g", class_="numeric"),
                    ui.tags.td(ui.div(ui.span(style=f"width:{share:.2f}%"), class_="share-track")),
                    ui.tags.td(f"{share:.0f}%", class_="numeric"),
                )
            )

        if warnings:
            summary = ui.div(
                ui.span("Review", class_="result-state"),
                ui.strong(f"{len(warnings)} item{'s' if len(warnings) != 1 else ''} to check"),
                *[ui.p(message) for message in warnings],
                class_="result-banner result-banner-warning",
            )
        else:
            summary = ui.div(
                icon("check"),
                ui.div(
                    ui.span("Balanced", class_="result-state"),
                    ui.strong("No target or structural flag"),
                ),
                class_="result-banner result-banner-ready",
            )

        primary_cards = (
            (
                balance_card(
                    "Total solids",
                    metrics.total_solids_pct,
                    solids_target,
                    "%",
                    20,
                    45,
                    1,
                ),
                balance_card("Sweetness · POD", metrics.pod, pod_target, "", 100, 280, 0),
                balance_card("Freeze softness · PAC", metrics.pac, pac_target, "", 240, 380, 0),
            )
            if is_sorbet
            else (
                balance_card("Fat", metrics.fat_pct, fat_target, "%", 5, 20, 1),
                balance_card("Sweetness · POD", metrics.pod, pod_target, "", 70, 160, 0),
                balance_card("Freeze softness · PAC", metrics.pac, pac_target, "", 180, 300, 0),
            )
        )
        diagnostic_chips = [
            ui.span(
                f"Fiber: {metrics.fiber_pct:.2f}% of mix",
                class_="diagnostic-chip",
            ),
            ui.span(
                f"Glucose/dextrose: {metrics.dextrose_share_pct:.1f}% of modeled sugar",
                class_="diagnostic-chip",
            ),
        ]
        if not is_sorbet:
            diagnostic_chips.insert(
                0,
                ui.span(
                    f"Lactose: {metrics.lactose_water_pct:.2f}% of water",
                    class_="diagnostic-chip",
                ),
            )

        return ui.TagList(
            ui.div(
                ui.span("Current batch"),
                ui.strong(f"{metrics.total_mass:.0f} g"),
                class_="batch-total",
            ),
            ui.div(
                *primary_cards,
                class_="balance-card-stack",
            ),
            summary,
            ui.tags.details(
                ui.tags.summary("Show full composition"),
                ui.tags.table(
                    ui.tags.thead(
                        ui.tags.tr(
                            ui.tags.th("Metric"),
                            ui.tags.th("Current"),
                            ui.tags.th("Guide"),
                            ui.tags.th("Status"),
                        )
                    ),
                    ui.tags.tbody(*metric_rows),
                    class_="results-table",
                ),
                ui.div(*diagnostic_chips, class_="diagnostic-row"),
                class_="result-details",
            ),
            ui.tags.details(
                ui.tags.summary("Show sugar blend"),
                ui.tags.table(
                    ui.tags.thead(
                        ui.tags.tr(
                            ui.tags.th("Component"),
                            ui.tags.th("Mass"),
                            ui.tags.th("Share"),
                            ui.tags.th("%"),
                        )
                    ),
                    ui.tags.tbody(*sugar_rows),
                    class_="sugar-table",
                ),
                class_="result-details",
            ),
        )

    def store_custom_ingredient(ingredient: Ingredient) -> None:
        """Add one session-local ingredient and refresh grouped selectors."""

        stored_lines = current_lines()
        library = dict(library_state.get())
        library[ingredient.ingredient_id] = ingredient
        recipe_state.set(stored_lines)
        library_state.set(library)
        custom_counter.set(custom_counter.get() + 1)
        ui.update_selectize(
            "add_ingredient",
            choices=ingredient_choices(library),
            selected=ingredient.ingredient_id,
            session=session,
        )

    @reactive.effect
    @reactive.event(input.save_fruit)
    def _save_fruit() -> None:
        counter = custom_counter.get()
        ingredient_id = f"user_{counter}"
        try:
            ingredient = ingredient_from_fruit_composition(
                ingredient_id=ingredient_id,
                name=str(input.fruit_name() or ""),
                fat=float(input.fruit_fat() or 0),
                water=float(input.fruit_water() or 0),
                sucrose=float(input.fruit_sucrose() or 0),
                glucose=float(input.fruit_glucose() or 0),
                fructose=float(input.fruit_fructose() or 0),
                fiber=float(input.fruit_fiber() or 0),
                other_solids=float(input.fruit_other() or 0),
                brix=float(input.fruit_brix() or 0),
            )
        except ValueError as exc:
            fruit_message.set(("error", str(exc)))
            return
        store_custom_ingredient(ingredient)
        fruit_message.set(
            (
                "success",
                (
                    f"Added {ingredient.name} for this browser session. "
                    "It is now selected in the calculator's add-ingredient control."
                ),
            )
        )

    @reactive.effect
    @reactive.event(input.save_chocolate)
    def _save_chocolate() -> None:
        counter = custom_counter.get()
        ingredient_id = f"user_{counter}"
        try:
            ingredient = ingredient_from_nutrition_label(
                ingredient_id=ingredient_id,
                name=str(input.chocolate_name() or ""),
                fat=float(input.chocolate_fat() or 0),
                carbohydrate=float(input.chocolate_carbohydrate() or 0),
                sugars=float(input.chocolate_sugars() or 0),
                protein=float(input.chocolate_protein() or 0),
                fibre=float(input.chocolate_fiber() or 0),
                salt=float(input.chocolate_salt() or 0),
                water=float(input.chocolate_water() or 0),
                sugar_component="sucrose",
                category="Chocolate & cocoa",
            )
        except ValueError as exc:
            chocolate_message.set(("error", str(exc)))
            return
        store_custom_ingredient(ingredient)
        chocolate_message.set(
            (
                "success",
                (
                    f"Added {ingredient.name} for this browser session. "
                    "It is now selected in the calculator's add-ingredient control."
                ),
            )
        )

    @reactive.effect
    @reactive.event(input.save_custom)
    def _save_custom() -> None:
        counter = custom_counter.get()
        ingredient_id = f"user_{counter}"
        try:
            if input.custom_mode() == "label":
                ingredient = ingredient_from_nutrition_label(
                    ingredient_id=ingredient_id,
                    name=str(input.custom_name() or ""),
                    fat=float(input.label_fat() or 0),
                    carbohydrate=float(input.label_carbohydrate() or 0),
                    sugars=float(input.label_sugars() or 0),
                    protein=float(input.label_protein() or 0),
                    fibre=float(input.label_fibre() or 0),
                    salt=float(input.label_salt() or 0),
                    water=float(input.label_water() or 0),
                    sugar_component=str(input.label_sugar_type() or "sucrose"),
                )
            else:
                ingredient = ingredient_from_composition(
                    ingredient_id=ingredient_id,
                    name=str(input.custom_name() or ""),
                    fat=float(input.direct_fat() or 0),
                    msnf=float(input.direct_msnf() or 0),
                    soluble_component=str(input.direct_component() or "sucrose"),
                    soluble_amount=float(input.direct_component_amount() or 0),
                    fiber=float(input.direct_fiber() or 0),
                    other_solids=float(input.direct_other() or 0),
                    salt=float(input.direct_salt() or 0),
                    alcohol=float(input.direct_alcohol() or 0),
                    gums=float(input.direct_gums() or 0),
                    water=float(input.direct_water() or 0),
                )
        except ValueError as exc:
            custom_message.set(("error", str(exc)))
            return

        store_custom_ingredient(ingredient)
        custom_message.set(
            (
                "success",
                (
                    f"Added {ingredient.name} for this browser session. "
                    "It is now available in the calculator."
                ),
            )
        )

    @render.ui
    def fruit_status():
        level, message = fruit_message.get()
        return ui.div(message, class_=f"inline-status inline-status-{level}")

    @render.ui
    def chocolate_status():
        level, message = chocolate_message.get()
        return ui.div(message, class_=f"inline-status inline-status-{level}")

    @render.ui
    def custom_status():
        level, message = custom_message.get()
        return ui.div(message, class_=f"inline-status inline-status-{level}")

    @render.ui
    def ingredient_library():
        rows = []
        for ingredient in library_state.get().values():
            rows.append(
                ui.tags.tr(
                    ui.tags.th(ingredient.name, scope="row"),
                    ui.tags.td(ingredient.category),
                    ui.tags.td(f"{ingredient.component('fat'):.2f}", class_="numeric"),
                    ui.tags.td(f"{ingredient.component('msnf'):.2f}", class_="numeric"),
                    ui.tags.td(f"{ingredient.component('water'):.2f}", class_="numeric"),
                    ui.tags.td(f"{ingredient.component('fiber'):.2f}", class_="numeric"),
                    ui.tags.td(f"{ingredient_pod_coefficient(ingredient):.3f}", class_="numeric"),
                    ui.tags.td(f"{ingredient_pac_coefficient(ingredient):.3f}", class_="numeric"),
                    ui.tags.td(ingredient.note or "Built-in assumption", class_="note-cell"),
                )
            )
        return ui.div(
            ui.tags.table(
                ui.tags.thead(
                    ui.tags.tr(
                        ui.tags.th("Ingredient"),
                        ui.tags.th("Category"),
                        ui.tags.th("Fat"),
                        ui.tags.th("MSNF"),
                        ui.tags.th("Water"),
                        ui.tags.th("Fiber"),
                        ui.tags.th("POD/g"),
                        ui.tags.th("PAC/g"),
                        ui.tags.th("Note"),
                    )
                ),
                ui.tags.tbody(*rows),
                class_="library-table",
            ),
            class_="table-scroll",
        )


app = App(app_ui, server)
