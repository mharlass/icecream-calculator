"""Pure-Python formulation engine for the ice cream dashboard.

The model contains no Shiny code. This keeps the formulation arithmetic independently
testable and compatible with Shinylive's browser-side Python runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import isfinite
from typing import Any

COMPONENT_FACTORS: dict[str, tuple[float, float]] = {
    "sucrose": (100.0, 100.0),
    "dextrose": (70.0, 190.0),
    "fructose": (170.0, 190.0),
    "invert_sugar": (130.0, 167.0),
    "atomized_glucose_40de": (50.0, 35.0),
    "glucose_syrup_42de": (55.0, 80.0),
    "honey_solids": (130.0, 146.0),
    "maltodextrin_15de": (17.0, 29.0),
    "inulin": (10.0, 65.0),
    "trehalose": (20.0, 100.0),
    "erythritol": (65.0, 280.0),
    "glycerol": (80.0, 370.0),
    # Derived from Underbelly's worked example: 70 g MSNF -> POD 6, PAC 38.
    "msnf": (8.3, 54.0),
    # Derived from molecular weight and ideal dissociation; practical approximation.
    "salt": (0.0, 1100.0),
    "alcohol": (0.0, 740.0),
}

SUGAR_COMPONENTS = {
    "sucrose",
    "dextrose",
    "fructose",
    "invert_sugar",
    "atomized_glucose_40de",
    "glucose_syrup_42de",
    "honey_solids",
    "trehalose",
    "erythritol",
    "glycerol",
}

NONFAT_SOLID_COMPONENTS = {
    "msnf",
    *SUGAR_COMPONENTS,
    "maltodextrin_15de",
    "inulin",
    "fiber",
    "other_solids",
    "salt",
    "gums",
}

SOLUBLE_COMPONENT_LABELS = {
    "sucrose": "Sucrose",
    "dextrose": "Dextrose",
    "fructose": "Fructose",
    "invert_sugar": "Invert sugar solids",
    "atomized_glucose_40de": "Atomized glucose 40DE",
    "glucose_syrup_42de": "Glucose syrup 42DE solids",
    "honey_solids": "Honey solids",
    "maltodextrin_15de": "Maltodextrin 15DE",
    "inulin": "Inulin",
    "trehalose": "Trehalose",
    "erythritol": "Erythritol",
    "glycerol": "Glycerol",
}

BASE_PRESET_INFO = {
    "no_cook": {
        "name": "No-cook dairy",
        "description": "A cold-blended dairy base using CMC, guar, and lambda carrageenan.",
        "process": "Blend cold, age, then freeze.",
    },
    "cooked_dairy": {
        "name": "Cooked dairy · no egg",
        "description": "An egg-free base with heat-activated locust bean gum.",
        "process": "Heat, cool quickly, age, then freeze.",
    },
    "yolk_custard": {
        "name": "Cooked custard · egg yolks",
        "description": "A richer custard with 5% egg yolk in the starting formula.",
        "process": "Temper the yolks, cook gently, cool quickly, age, then freeze.",
    },
    "whole_egg_custard": {
        "name": "Cooked custard · whole eggs",
        "description": "A lighter egg custard with 8% whole egg in the starting formula.",
        "process": "Temper the eggs, cook gently, cool quickly, age, then freeze.",
    },
    "strawberry_sorbet": {
        "name": "Strawberry sorbet",
        "description": (
            "Underbelly's high-fruit, lower-sweetness formula, recomputed here with the "
            "calculator's USDA strawberry reference."
        ),
        "process": "Blend, rest cold, then freeze. Replace the fruit data for the actual Brix.",
    },
}

TARGET_PROFILE_INFO = {
    "Creami / Pacojet": {
        "name": "Ice cream · CREAMi or Pacojet",
        "product_style": "ice_cream",
    },
    "Churned machine": {
        "name": "Ice cream · churned machine",
        "product_style": "ice_cream",
    },
    "Fruit sorbet · experimental": {
        "name": "Fruit sorbet · experimental",
        "product_style": "sorbet",
    },
}


@dataclass(frozen=True)
class Ingredient:
    """An ingredient expressed as component grams per 100 g.

    Attributes:
        ingredient_id: Stable identifier used by formula rows.
        name: Reader-facing ingredient name.
        category: Broad grouping shown in the ingredient library.
        components: Component grams per 100 g of ingredient.
        note: Provenance or formulation caveat.
        custom: Whether the user defined this ingredient.
    """

    ingredient_id: str
    name: str
    category: str
    components: dict[str, float]
    note: str = ""
    custom: bool = False

    def component(self, name: str) -> float:
        """Return component grams per 100 g, defaulting to zero."""

        return float(self.components.get(name, 0.0))

    @property
    def accounted_mass(self) -> float:
        """Return the sum of all declared components per 100 g."""

        return sum(self.components.values())

    def to_dict(self) -> dict[str, Any]:
        """Serialize the ingredient for JSON export."""

        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Ingredient:
        """Create an ingredient from validated JSON-compatible data."""

        return cls(
            ingredient_id=str(payload["ingredient_id"]),
            name=str(payload["name"]),
            category=str(payload.get("category", "Custom")),
            components={
                str(name): float(value)
                for name, value in dict(payload.get("components", {})).items()
            },
            note=str(payload.get("note", "")),
            custom=bool(payload.get("custom", True)),
        )


@dataclass(frozen=True)
class RecipeLine:
    """One ingredient and its quantity in a formulation."""

    ingredient_id: str
    grams: float
    free: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize the formula line for JSON export."""

        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RecipeLine:
        """Create a formula line from JSON-compatible data."""

        return cls(
            ingredient_id=str(payload["ingredient_id"]),
            grams=float(payload["grams"]),
            free=bool(payload.get("free", False)),
        )


@dataclass(frozen=True)
class Targets:
    """Selected formulation targets for recipe optimization.

    ``total_mass`` is always enforced. A composition target is included only when
    its value is not ``None``.
    """

    total_mass: float
    fat_pct: float | None = None
    msnf_pct: float | None = None
    total_solids_pct: float | None = None
    pod: float | None = None
    pac: float | None = None


@dataclass(frozen=True)
class OptimizationResult:
    """Optimized recipe and remaining differences from the selected targets."""

    lines: list[RecipeLine]
    target_errors: dict[str, float]


@dataclass(frozen=True)
class Metrics:
    """Computed formulation metrics, normalized to the current batch mass."""

    total_mass: float = 0.0
    fat_pct: float = 0.0
    msnf_pct: float = 0.0
    modeled_sugars_pct: float = 0.0
    nonfat_solids_pct: float = 0.0
    total_solids_pct: float = 0.0
    water_pct: float = 0.0
    fiber_pct: float = 0.0
    gums_pct: float = 0.0
    pod: float = 0.0
    pac: float = 0.0
    pac_per_100g: float = 0.0
    absolute_pac: float = 0.0
    dextrose_share_pct: float = 0.0
    lactose_water_pct: float = 0.0
    component_grams: dict[str, float] = field(default_factory=dict)
    sugar_grams: dict[str, float] = field(default_factory=dict)

    @property
    def added_sugars_pct(self) -> float:
        """Return the legacy sugar metric name for compatibility."""

        return self.modeled_sugars_pct


class FormulationError(ValueError):
    """Raised when a formulation cannot be optimized safely."""


def _cream_components(fat_pct: float) -> dict[str, float]:
    """Estimate cream MSNF from Underbelly's 36% fat / 5.6% MSNF anchor."""

    msnf = 5.6 * (100.0 - fat_pct) / 64.0
    return {"fat": fat_pct, "msnf": msnf, "water": 100.0 - fat_pct - msnf}


def _pure(component: str, *, water: float = 0.0) -> dict[str, float]:
    """Return a simple one-component ingredient composition."""

    return {component: 100.0 - water, **({"water": water} if water else {})}


def default_library() -> dict[str, Ingredient]:
    """Return the editable seed ingredient library.

    Returns:
        A mapping from stable ingredient ID to its composition.
    """

    ingredients = [
        Ingredient("water", "Water", "Water & fruit", {"water": 100.0}),
        Ingredient(
            "whole_milk_35",
            "Whole milk · 3.5% fat",
            "Dairy",
            {"fat": 3.5, "msnf": 8.8, "water": 87.7},
        ),
        Ingredient(
            "whole_milk_38",
            "Whole milk · 3.8% fat",
            "Dairy",
            {"fat": 3.8, "msnf": 8.8, "water": 87.4},
        ),
        Ingredient(
            "milk_15",
            "Semi-skim milk · 1.5% fat",
            "Dairy",
            {"fat": 1.5, "msnf": 9.0, "water": 89.5},
        ),
        Ingredient(
            "skim_milk",
            "Skim milk · 0.1% fat",
            "Dairy",
            {"fat": 0.1, "msnf": 9.0, "water": 90.9},
        ),
        *[
            Ingredient(
                f"cream_{int(fat)}",
                f"Cream · {fat:.0f}% fat",
                "Dairy",
                _cream_components(fat),
                "MSNF estimated from Underbelly's 36% cream anchor.",
            )
            for fat in (32.0, 35.0, 36.0, 38.0, 40.0)
        ],
        Ingredient(
            "nonfat_dry_milk",
            "Nonfat dry milk",
            "Dairy solids",
            {"msnf": 100.0},
            "Underbelly convention. Check the package; real powder is often 96–97% solids.",
        ),
        Ingredient(
            "whole_milk_powder",
            "Whole milk powder",
            "Dairy solids",
            {"fat": 26.0, "msnf": 71.0, "water": 3.0},
        ),
        Ingredient(
            "egg_yolk",
            "Egg yolk",
            "Eggs & emulsifiers",
            {"fat": 23.0, "other_solids": 27.0, "water": 50.0},
        ),
        Ingredient(
            "whole_egg",
            "Whole egg",
            "Eggs & emulsifiers",
            {"fat": 9.5, "other_solids": 14.3, "water": 76.2},
            "Approximate raw whole-egg composition. Use pasteurized egg where appropriate.",
        ),
        Ingredient("sucrose", "Sucrose", "Sweetener", _pure("sucrose")),
        Ingredient("dextrose", "Dextrose", "Sweetener", _pure("dextrose")),
        Ingredient("fructose", "Fructose", "Sweetener", _pure("fructose")),
        Ingredient("inulin", "Inulin", "Bulking solid", _pure("inulin")),
        Ingredient(
            "maltodextrin_15de",
            "Maltodextrin · 15DE",
            "Bulking solid",
            _pure("maltodextrin_15de"),
        ),
        Ingredient(
            "atomized_glucose_40de",
            "Atomized glucose · 40DE",
            "Sweetener",
            _pure("atomized_glucose_40de"),
        ),
        Ingredient("trehalose", "Trehalose", "Sweetener", _pure("trehalose")),
        Ingredient("erythritol", "Erythritol", "Sweetener", _pure("erythritol")),
        Ingredient("glycerol", "Glycerol", "Sweetener", _pure("glycerol")),
        Ingredient(
            "invert_syrup",
            "Invert syrup · 80% solids",
            "Sweetener",
            {"invert_sugar": 80.0, "water": 20.0},
        ),
        Ingredient(
            "honey",
            "Honey · 82% solids",
            "Sweetener",
            {"honey_solids": 82.0, "water": 18.0},
        ),
        Ingredient(
            "glucose_syrup_42de",
            "Glucose syrup · 42DE / 75% solids",
            "Sweetener",
            {"glucose_syrup_42de": 75.0, "water": 25.0},
        ),
        Ingredient(
            "soy_lecithin",
            "Soy lecithin powder",
            "Eggs & emulsifiers",
            {"other_solids": 100.0},
        ),
        Ingredient(
            "sunflower_lecithin",
            "Sunflower lecithin powder",
            "Eggs & emulsifiers",
            {"other_solids": 100.0},
        ),
        Ingredient(
            "mono_diglycerides",
            "Mono- and diglycerides",
            "Eggs & emulsifiers",
            {"other_solids": 100.0},
            "Use the supplier's specification and recommended dose.",
        ),
        Ingredient(
            "polysorbate_80",
            "Polysorbate 80",
            "Eggs & emulsifiers",
            {"other_solids": 100.0},
            "Very effective at low concentration. Use a 0.01 g scale and supplier guidance.",
        ),
        Ingredient("salt", "Fine salt", "Salt", _pure("salt")),
        Ingredient("guar", "Guar gum", "Stabilizer", _pure("gums")),
        Ingredient("locust_bean_gum", "Locust bean gum", "Stabilizer", _pure("gums")),
        Ingredient(
            "lambda_carrageenan",
            "Lambda carrageenan",
            "Stabilizer",
            _pure("gums"),
        ),
        Ingredient("cmc", "CMC", "Stabilizer", _pure("gums")),
        Ingredient("xanthan", "Xanthan gum", "Stabilizer", _pure("gums")),
        Ingredient("gelatin", "Gelatin", "Stabilizer", _pure("gums")),
        Ingredient("tara_gum", "Tara gum", "Stabilizer", _pure("gums")),
        Ingredient("sodium_alginate", "Sodium alginate", "Stabilizer", _pure("gums")),
        Ingredient("kappa_carrageenan", "Kappa carrageenan", "Stabilizer", _pure("gums")),
        Ingredient(
            "collagen_peptides",
            "Hydrolyzed collagen peptides",
            "Protein & body",
            {"other_solids": 100.0},
            "Not equivalent to gelling gelatin. Performance depends on peptide size and product.",
        ),
        Ingredient(
            "strawberry_puree",
            "Strawberry purée · unsweetened reference",
            "Fruit & purée",
            {
                "fat": 0.22,
                "sucrose": 0.00,
                "dextrose": 2.24,
                "fructose": 2.62,
                "other_solids": 4.12,
                "water": 90.80,
            },
            "USDA Foundation Foods April 2026 mean for raw strawberries (FDC 2346409). "
            "The record has no fiber value, so fiber remains inside residual other solids. "
            "Cultivar, ripeness, processing, and Brix can materially change a real purée.",
        ),
        Ingredient(
            "mango_puree",
            "Mango purée · unsweetened reference",
            "Fruit & purée",
            {
                "fat": 0.38,
                "sucrose": 6.97,
                "dextrose": 2.01,
                "fructose": 4.68,
                "fiber": 1.60,
                "other_solids": 0.90,
                "water": 83.46,
            },
            "USDA reference composition for raw mango. Cultivar, ripeness, processing, "
            "and measured Brix can materially change a real purée.",
        ),
        Ingredient(
            "cocoa_powder",
            "Cocoa powder · unsweetened reference",
            "Chocolate & cocoa",
            {
                "fat": 13.70,
                "sucrose": 1.75,
                "fiber": 37.00,
                "other_solids": 44.55,
                "water": 3.00,
            },
            "USDA reference for unsweetened cocoa powder. Fat and fiber vary widely by "
            "brand and cocoa treatment; use the package values for precise work.",
        ),
        Ingredient(
            "dark_chocolate_70",
            "Dark chocolate · 70% approximate",
            "Chocolate & cocoa",
            {"fat": 43.0, "sucrose": 29.0, "other_solids": 27.0, "water": 1.0},
            "Approximation only; replace with the package values for precise work.",
        ),
        Ingredient(
            "spirit_40",
            "Spirit · 40% ABV",
            "Flavor",
            {"alcohol": 40.0, "water": 60.0},
        ),
    ]
    ingredients.extend(
        Ingredient(
            f"custom_{index}",
            f"Custom ingredient {index}",
            "Custom",
            {"water": 100.0},
            "Define this slot in the Ingredients tab.",
            custom=True,
        )
        for index in range(1, 5)
    )
    return {ingredient.ingredient_id: ingredient for ingredient in ingredients}


def seed_recipe() -> list[RecipeLine]:
    """Return the balanced no-cook Ninja Creami seed recipe."""

    return [
        RecipeLine("whole_milk_35", 466.0, True),
        RecipeLine("cream_35", 339.0, True),
        RecipeLine("nonfat_dry_milk", 55.0, True),
        RecipeLine("sucrose", 65.0, True),
        RecipeLine("dextrose", 50.0, True),
        RecipeLine("inulin", 20.0),
        RecipeLine("soy_lecithin", 2.0),
        RecipeLine("salt", 1.2),
        RecipeLine("cmc", 0.8),
        RecipeLine("guar", 0.6),
        RecipeLine("lambda_carrageenan", 0.4),
    ]


def base_recipe(preset_id: str) -> list[RecipeLine]:
    """Return a balanced 1 kg starting formula for a supported base style.

    Args:
        preset_id: One of the keys in ``BASE_PRESET_INFO``.

    Returns:
        A new recipe list with suitable starting rows available to the optimizer.

    Raises:
        ValueError: If ``preset_id`` does not identify a supported base style.
    """

    recipes = {
        "no_cook": seed_recipe(),
        "cooked_dairy": [
            RecipeLine("whole_milk_35", 466.0, True),
            RecipeLine("cream_35", 339.0, True),
            RecipeLine("nonfat_dry_milk", 55.0, True),
            RecipeLine("sucrose", 65.0, True),
            RecipeLine("dextrose", 50.0, True),
            RecipeLine("inulin", 20.0),
            RecipeLine("soy_lecithin", 2.0),
            RecipeLine("salt", 1.2),
            RecipeLine("locust_bean_gum", 0.9),
            RecipeLine("guar", 0.5),
            RecipeLine("lambda_carrageenan", 0.4),
        ],
        "yolk_custard": [
            RecipeLine("whole_milk_35", 468.137, True),
            RecipeLine("cream_35", 306.043, True),
            RecipeLine("nonfat_dry_milk", 49.398, True),
            RecipeLine("sucrose", 64.302, True),
            RecipeLine("dextrose", 59.620, True),
            RecipeLine("egg_yolk", 50.0),
            RecipeLine("salt", 1.1),
            RecipeLine("locust_bean_gum", 0.7),
            RecipeLine("guar", 0.4),
            RecipeLine("lambda_carrageenan", 0.3),
        ],
        "whole_egg_custard": [
            RecipeLine("whole_milk_35", 418.596, True),
            RecipeLine("cream_35", 322.140, True),
            RecipeLine("nonfat_dry_milk", 52.842, True),
            RecipeLine("sucrose", 64.302, True),
            RecipeLine("dextrose", 59.620, True),
            RecipeLine("whole_egg", 80.0),
            RecipeLine("salt", 1.1),
            RecipeLine("locust_bean_gum", 0.7),
            RecipeLine("guar", 0.4),
            RecipeLine("lambda_carrageenan", 0.3),
        ],
        "strawberry_sorbet": [
            RecipeLine("strawberry_puree", 750.0, True),
            RecipeLine("water", 51.0, True),
            RecipeLine("dextrose", 42.0, True),
            RecipeLine("atomized_glucose_40de", 65.0, True),
            RecipeLine("trehalose", 40.0, True),
            RecipeLine("erythritol", 20.0),
            RecipeLine("inulin", 27.0),
            RecipeLine("cmc", 2.0),
            RecipeLine("guar", 1.0),
            RecipeLine("lambda_carrageenan", 1.0),
            RecipeLine("salt", 1.0),
        ],
    }
    if preset_id not in recipes:
        expected = ", ".join(BASE_PRESET_INFO)
        raise ValueError(f"Unknown base preset {preset_id!r}; expected one of: {expected}.")
    return list(recipes[preset_id])


def ingredient_pod_coefficient(ingredient: Ingredient) -> float:
    """Return sucrose-equivalent POD contributed by one ingredient gram."""

    return sum(
        ingredient.component(component) * factors[0] / 10_000.0
        for component, factors in COMPONENT_FACTORS.items()
    )


def ingredient_pac_coefficient(ingredient: Ingredient) -> float:
    """Return sucrose-equivalent PAC contributed by one ingredient gram."""

    return sum(
        ingredient.component(component) * factors[1] / 10_000.0
        for component, factors in COMPONENT_FACTORS.items()
    )


def calculate_recipe(
    lines: list[RecipeLine],
    library: dict[str, Ingredient],
) -> Metrics:
    """Calculate composition, sweetness, and freezing-point metrics.

    Args:
        lines: Ingredient quantities in the batch.
        library: Ingredients keyed by stable ID.

    Returns:
        Metrics normalized to the actual total batch mass.

    Raises:
        ValueError: If a formula references an unknown ingredient.
    """

    total_mass = sum(line.grams for line in lines)
    if total_mass <= 0:
        return Metrics(total_mass=total_mass)

    component_grams: dict[str, float] = {}
    pod_absolute = 0.0
    pac_absolute = 0.0
    for line in lines:
        if line.ingredient_id not in library:
            raise ValueError(f"Unknown ingredient: {line.ingredient_id!r}")
        ingredient = library[line.ingredient_id]
        for component, amount_per_100g in ingredient.components.items():
            component_grams[component] = (
                component_grams.get(component, 0.0) + line.grams * amount_per_100g / 100.0
            )
        pod_absolute += line.grams * ingredient_pod_coefficient(ingredient)
        pac_absolute += line.grams * ingredient_pac_coefficient(ingredient)

    fat_grams = component_grams.get("fat", 0.0)
    msnf_grams = component_grams.get("msnf", 0.0)
    water_grams = component_grams.get("water", 0.0)
    gums_grams = component_grams.get("gums", 0.0)
    fiber_grams = component_grams.get("fiber", 0.0)
    sugar_grams = {
        component: component_grams.get(component, 0.0)
        for component in SUGAR_COMPONENTS
        if component_grams.get(component, 0.0) > 0
    }
    modeled_sugars_grams = sum(sugar_grams.values())
    nonfat_solids_grams = sum(
        component_grams.get(component, 0.0) for component in NONFAT_SOLID_COMPONENTS
    )

    scale = 100.0 / total_mass
    water_pct = water_grams * scale
    pac = pac_absolute * 1000.0 / total_mass
    lactose_grams = 0.52 * msnf_grams
    return Metrics(
        total_mass=total_mass,
        fat_pct=fat_grams * scale,
        msnf_pct=msnf_grams * scale,
        modeled_sugars_pct=modeled_sugars_grams * scale,
        nonfat_solids_pct=nonfat_solids_grams * scale,
        total_solids_pct=(fat_grams + nonfat_solids_grams) * scale,
        water_pct=water_pct,
        fiber_pct=fiber_grams * scale,
        gums_pct=gums_grams * scale,
        pod=pod_absolute * 1000.0 / total_mass,
        pac=pac,
        pac_per_100g=pac / 10.0,
        absolute_pac=pac / (water_pct / 100.0) if water_pct else 0.0,
        dextrose_share_pct=(
            100.0 * sugar_grams.get("dextrose", 0.0) / modeled_sugars_grams
            if modeled_sugars_grams
            else 0.0
        ),
        lactose_water_pct=(100.0 * lactose_grams / water_grams if water_grams else 0.0),
        component_grams=component_grams,
        sugar_grams=sugar_grams,
    )


def diagnose_recipe(
    metrics: Metrics,
    *,
    fat_cap: float = 15.0,
    target_set: str = "Creami / Pacojet",
) -> list[str]:
    """Return plain-language safety and feasibility warnings."""

    warnings: list[str] = []
    if metrics.total_mass <= 0:
        return ["Add at least one ingredient with a positive quantity."]
    is_sorbet = target_set == "Fruit sorbet · experimental"
    if not is_sorbet:
        if metrics.fat_pct > fat_cap:
            warnings.append(f"Fat is {metrics.fat_pct:.1f}%, above your {fat_cap:.1f}% cap.")
        if metrics.lactose_water_pct > 10.0:
            warnings.append(
                "Estimated lactose exceeds 10% of the water phase; sandy lactose crystals "
                "become more likely."
            )
        if metrics.dextrose_share_pct > 50.0:
            warnings.append(
                "Dextrose exceeds 50% of the modeled sugar blend, above Underbelly's "
                "suggested ceiling for dairy ice cream."
            )
    solids_range = (25.0, 33.0) if is_sorbet else (35.0, 45.0)
    if not solids_range[0] <= metrics.total_solids_pct <= solids_range[1]:
        warnings.append(
            f"Total solids are {metrics.total_solids_pct:.1f}%; the active starting range "
            f"is {solids_range[0]:g}% to {solids_range[1]:g}%."
        )
    return warnings


_OPTIMIZATION_TOLERANCES = {
    "fat_pct": 1.0,
    "msnf_pct": 1.0,
    "total_solids_pct": 2.0,
    "pod": 5.0,
    "pac": 5.0,
}


def _project_to_simplex(values: list[float], total: float) -> list[float]:
    """Return the closest nonnegative values whose sum is ``total``."""

    if total <= 0:
        return [0.0 for _ in values]
    ordered = sorted(values, reverse=True)
    running_total = 0.0
    threshold = 0.0
    for rank, value in enumerate(ordered, start=1):
        running_total += value
        candidate = (running_total - total) / rank
        if value > candidate:
            threshold = candidate
    return [max(0.0, value - threshold) for value in values]


def _ingredient_metric_coefficient(
    ingredient: Ingredient,
    target_name: str,
    total_mass: float,
) -> float:
    """Return the normalized metric change contributed by one ingredient gram."""

    if target_name == "fat_pct":
        return ingredient.component("fat") / total_mass
    if target_name == "msnf_pct":
        return ingredient.component("msnf") / total_mass
    if target_name == "total_solids_pct":
        solids_per_100g = ingredient.component("fat") + sum(
            ingredient.component(component) for component in NONFAT_SOLID_COMPONENTS
        )
        return solids_per_100g / total_mass
    if target_name == "pod":
        return ingredient_pod_coefficient(ingredient) * 1000.0 / total_mass
    if target_name == "pac":
        return ingredient_pac_coefficient(ingredient) * 1000.0 / total_mass
    expected = ", ".join(_OPTIMIZATION_TOLERANCES)
    raise ValueError(f"Unknown optimization target {target_name!r}; expected one of: {expected}.")


def _selected_target_values(targets: Targets) -> dict[str, float]:
    """Return validated composition targets selected by the caller."""

    selected = {
        name: value
        for name in _OPTIMIZATION_TOLERANCES
        if (value := getattr(targets, name)) is not None
    }
    if not selected:
        raise FormulationError("Select at least one composition target to optimize.")
    for name, value in selected.items():
        if not isfinite(value) or value < 0:
            raise FormulationError(
                f"Target {name} must be a finite nonnegative value; got {value!r}."
            )
    return selected


def optimize_recipe(
    lines: list[RecipeLine],
    library: dict[str, Ingredient],
    targets: Targets,
) -> OptimizationResult:
    """Optimize selected ingredient quantities against selected formulation targets.

    Args:
        lines: Current formula. Rows with ``free=True`` may be changed.
        library: Ingredients keyed by stable ID.
        targets: Desired batch mass and optional composition targets.

    Returns:
        Optimized nonnegative quantities and signed target errors.

    Raises:
        FormulationError: If there are no adjustable rows or selected targets, or
            the locked rows already exceed the requested batch mass.
    """

    free_indices = [index for index, line in enumerate(lines) if line.free]
    if not free_indices:
        raise FormulationError("Select at least one ingredient row for auto-adjustment.")
    if not isfinite(targets.total_mass) or targets.total_mass <= 0:
        raise FormulationError(
            f"Target mass must be a finite positive value; got {targets.total_mass!r}."
        )
    selected_targets = _selected_target_values(targets)
    unknown = [line.ingredient_id for line in lines if line.ingredient_id not in library]
    if unknown:
        raise ValueError(f"Unknown ingredient: {unknown[0]!r}")
    invalid_lines = [
        (line.ingredient_id, line.grams)
        for line in lines
        if not isfinite(line.grams) or line.grams < 0
    ]
    if invalid_lines:
        ingredient_id, grams = invalid_lines[0]
        raise FormulationError(
            f"Ingredient {ingredient_id!r} must have a finite nonnegative quantity; got {grams!r}."
        )

    locked_mass = sum(line.grams for line in lines if not line.free)
    free_mass = targets.total_mass - locked_mass
    if free_mass < -1e-8:
        raise FormulationError(
            f"Locked rows already total {locked_mass:.1f} g, above the "
            f"{targets.total_mass:.1f} g batch target."
        )
    free_mass = max(0.0, free_mass)
    free_ingredients = [library[lines[index].ingredient_id] for index in free_indices]
    locked_lines = [line for line in lines if not line.free]
    target_rows = [
        [
            _ingredient_metric_coefficient(ingredient, name, targets.total_mass)
            / _OPTIMIZATION_TOLERANCES[name]
            for ingredient in free_ingredients
        ]
        for name in selected_targets
    ]
    locked_contributions = {
        name: sum(
            line.grams
            * _ingredient_metric_coefficient(
                library[line.ingredient_id],
                name,
                targets.total_mass,
            )
            for line in locked_lines
        )
        for name in selected_targets
    }
    scaled_rhs = [
        (target - locked_contributions[name]) / _OPTIMIZATION_TOLERANCES[name]
        for name, target in selected_targets.items()
    ]

    quantities = _project_to_simplex(
        [max(0.0, lines[index].grams) for index in free_indices],
        free_mass,
    )
    accelerated = quantities[:]
    momentum = 1.0
    lipschitz = 2.0 * sum(
        sum(coefficient * coefficient for coefficient in row) for row in target_rows
    )
    if lipschitz > 0:
        step = 1.0 / lipschitz
        for _ in range(20_000):
            residuals = [
                sum(
                    coefficient * value for coefficient, value in zip(row, accelerated, strict=True)
                )
                - rhs
                for row, rhs in zip(target_rows, scaled_rhs, strict=True)
            ]
            gradient = [
                2.0
                * sum(
                    row[column] * residual
                    for row, residual in zip(target_rows, residuals, strict=True)
                )
                for column in range(len(free_indices))
            ]
            updated = _project_to_simplex(
                [
                    value - step * derivative
                    for value, derivative in zip(accelerated, gradient, strict=True)
                ],
                free_mass,
            )
            if (
                max(
                    abs(value - previous)
                    for value, previous in zip(updated, quantities, strict=True)
                )
                < 1e-9
            ):
                quantities = updated
                break
            next_momentum = (1.0 + (1.0 + 4.0 * momentum * momentum) ** 0.5) / 2.0
            accelerated = [
                value + (momentum - 1.0) / next_momentum * (value - previous)
                for value, previous in zip(updated, quantities, strict=True)
            ]
            quantities = updated
            momentum = next_momentum

    result = lines[:]
    for index, solved_grams in zip(free_indices, quantities, strict=True):
        result[index] = RecipeLine(
            ingredient_id=result[index].ingredient_id,
            grams=max(0.0, solved_grams),
            free=True,
        )
    metrics = calculate_recipe(result, library)
    target_errors = {
        name: getattr(metrics, name) - target for name, target in selected_targets.items()
    }
    return OptimizationResult(lines=result, target_errors=target_errors)


def scale_recipe(lines: list[RecipeLine], target_mass: float) -> list[RecipeLine]:
    """Scale all quantities proportionally to a target batch mass."""

    current_mass = sum(line.grams for line in lines)
    if current_mass <= 0:
        raise ValueError(f"Cannot scale a formula with total mass {current_mass!r}; expected > 0.")
    if target_mass <= 0:
        raise ValueError(f"Target mass must be positive; got {target_mass!r}.")
    factor = target_mass / current_mass
    return [RecipeLine(line.ingredient_id, line.grams * factor, line.free) for line in lines]


def ingredient_from_nutrition_label(
    *,
    ingredient_id: str,
    name: str,
    fat: float,
    carbohydrate: float,
    sugars: float,
    protein: float,
    fibre: float,
    salt: float,
    water: float,
    sugar_component: str = "sucrose",
    category: str = "Custom",
) -> Ingredient:
    """Create a custom ingredient from European-style per-100 g label values.

    Carbohydrate is treated as excluding fibre. Sugars are treated as part of
    carbohydrate and assigned to the selected soluble component. A water value of
    zero asks the model to infer water by difference.

    Raises:
        ValueError: If values are negative, sugars exceed carbohydrate, the sugar
            component is unsupported, or declared components exceed 100 g.
    """

    values = {
        "fat": fat,
        "carbohydrate": carbohydrate,
        "sugars": sugars,
        "protein": protein,
        "fibre": fibre,
        "salt": salt,
        "water": water,
    }
    negative = {key: value for key, value in values.items() if value < 0}
    if negative:
        key, value = next(iter(negative.items()))
        raise ValueError(f"{key} must be non-negative; got {value!r}.")
    if sugars > carbohydrate:
        raise ValueError(
            f"Sugars ({sugars:g}) cannot exceed carbohydrate ({carbohydrate:g}) per 100 g."
        )
    if sugar_component not in SOLUBLE_COMPONENT_LABELS:
        raise ValueError(f"Unsupported sugar component: {sugar_component!r}.")
    if not name.strip():
        raise ValueError("Custom ingredient name cannot be blank.")

    other_solids = carbohydrate - sugars + protein
    declared_without_water = fat + sugars + fibre + other_solids + salt
    resolved_water = 100.0 - declared_without_water if water == 0 else water
    total = declared_without_water + resolved_water
    if total > 100.5:
        raise ValueError(
            f"Declared components total {total:.1f} g per 100 g; expected at most 100 g."
        )
    # Labels omit ash and rounding residuals. Treat any positive gap as other solids.
    other_solids += max(0.0, 100.0 - total)
    return Ingredient(
        ingredient_id=ingredient_id,
        name=name.strip(),
        category=category,
        components={
            "fat": fat,
            sugar_component: sugars,
            "fiber": fibre,
            "other_solids": other_solids,
            "salt": salt,
            "water": resolved_water,
        },
        note=(
            "Mapped from a nutrition label. Carbohydrate excludes fibre. Label sugars "
            f"are treated as {SOLUBLE_COMPONENT_LABELS[sugar_component].lower()}."
        ),
        custom=True,
    )


def ingredient_from_fruit_composition(
    *,
    ingredient_id: str,
    name: str,
    fat: float,
    water: float,
    sucrose: float,
    glucose: float,
    fructose: float,
    fiber: float,
    other_solids: float,
    brix: float = 0.0,
) -> Ingredient:
    """Create a fruit or purée ingredient from per-100 g composition data.

    Glucose is mapped to the model's dextrose component because both describe
    D-glucose for POD/PAC purposes. A water value of zero asks the model to infer
    water by difference. Any positive rounding gap is assigned to other solids.
    Brix is recorded as provenance but is not used as a substitute for the entered
    sugar split.

    Raises:
        ValueError: If values are negative, Brix is outside 0–100, the name is
            blank, or declared components exceed 100 g.
    """

    values = {
        "fat": fat,
        "water": water,
        "sucrose": sucrose,
        "glucose": glucose,
        "fructose": fructose,
        "fiber": fiber,
        "other_solids": other_solids,
        "brix": brix,
    }
    negative = {key: value for key, value in values.items() if value < 0}
    if negative:
        key, value = next(iter(negative.items()))
        raise ValueError(f"{key} must be non-negative; got {value!r}.")
    if brix > 100:
        raise ValueError(f"Brix must be between 0 and 100; got {brix!r}.")
    if not name.strip():
        raise ValueError("Fruit or purée name cannot be blank.")

    declared_without_water = fat + sucrose + glucose + fructose + fiber + other_solids
    resolved_water = 100.0 - declared_without_water if water == 0 else water
    total = declared_without_water + resolved_water
    if total > 100.5:
        raise ValueError(
            f"Declared components total {total:.1f} g per 100 g; expected at most 100 g."
        )
    resolved_other_solids = other_solids + max(0.0, 100.0 - total)
    brix_note = f" Entered Brix: {brix:g} °Bx." if brix else ""
    return Ingredient(
        ingredient_id=ingredient_id,
        name=name.strip(),
        category="Fruit & purée",
        components={
            "fat": fat,
            "sucrose": sucrose,
            "dextrose": glucose,
            "fructose": fructose,
            "fiber": fiber,
            "other_solids": resolved_other_solids,
            "water": resolved_water,
        },
        note=(
            "User-supplied fruit composition. Glucose is modeled with the dextrose "
            "POD/PAC factors. Fiber contributes to total solids, but its water binding "
            f"and particle texture are not predicted.{brix_note}"
        ),
        custom=True,
    )


def ingredient_from_composition(
    *,
    ingredient_id: str,
    name: str,
    fat: float,
    msnf: float,
    soluble_component: str,
    soluble_amount: float,
    fiber: float,
    other_solids: float,
    salt: float,
    alcohol: float,
    gums: float,
    water: float,
    category: str = "Custom",
) -> Ingredient:
    """Create a custom ingredient from direct component assignments per 100 g.

    A water value of zero asks the model to infer water by difference. Any small
    positive rounding gap is assigned to other solids.

    Raises:
        ValueError: If values are invalid or exceed 100 g in total.
    """

    values = {
        "fat": fat,
        "msnf": msnf,
        "soluble_amount": soluble_amount,
        "fiber": fiber,
        "other_solids": other_solids,
        "salt": salt,
        "alcohol": alcohol,
        "gums": gums,
        "water": water,
    }
    negative = {key: value for key, value in values.items() if value < 0}
    if negative:
        key, value = next(iter(negative.items()))
        raise ValueError(f"{key} must be non-negative; got {value!r}.")
    if soluble_component not in SOLUBLE_COMPONENT_LABELS:
        raise ValueError(f"Unsupported soluble component: {soluble_component!r}.")
    if not name.strip():
        raise ValueError("Custom ingredient name cannot be blank.")

    declared_without_water = (
        fat + msnf + soluble_amount + fiber + other_solids + salt + alcohol + gums
    )
    resolved_water = 100.0 - declared_without_water if water == 0 else water
    total = declared_without_water + resolved_water
    if total > 100.5:
        raise ValueError(
            f"Declared components total {total:.1f} g per 100 g; expected at most 100 g."
        )
    resolved_other_solids = other_solids + max(0.0, 100.0 - total)
    return Ingredient(
        ingredient_id=ingredient_id,
        name=name.strip(),
        category=category,
        components={
            "fat": fat,
            "msnf": msnf,
            soluble_component: soluble_amount,
            "fiber": fiber,
            "other_solids": resolved_other_solids,
            "salt": salt,
            "alcohol": alcohol,
            "gums": gums,
            "water": resolved_water,
        },
        note="Direct component composition supplied by the user.",
        custom=True,
    )


def target_ranges(
    target_set: str,
    *,
    fat_cap: float = 15.0,
) -> dict[str, tuple[float, float] | None]:
    """Return display target ranges for the active production method."""

    if target_set not in TARGET_PROFILE_INFO:
        expected = ", ".join(TARGET_PROFILE_INFO)
        raise ValueError(f"Unknown target profile {target_set!r}; expected one of: {expected}.")
    if target_set == "Fruit sorbet · experimental":
        return {
            "fat_pct": None,
            "msnf_pct": None,
            "modeled_sugars_pct": None,
            "nonfat_solids_pct": (25.0, 33.0),
            "total_solids_pct": (25.0, 33.0),
            "water_pct": (67.0, 75.0),
            "fiber_pct": None,
            "gums_pct": None,
            "pod": (140.0, 200.0),
            "pac": (300.0, 340.0),
        }
    pac_range = (245.0, 255.0) if target_set == "Creami / Pacojet" else (220.0, 230.0)
    return {
        "fat_pct": (12.0, fat_cap),
        "msnf_pct": (10.0, 12.0),
        "modeled_sugars_pct": (11.0, 14.0),
        "nonfat_solids_pct": (22.0, 25.0),
        "total_solids_pct": (37.0, 42.0),
        "water_pct": (58.0, 63.0),
        "fiber_pct": None,
        "gums_pct": (0.15, 0.20),
        "pod": (110.0, 120.0),
        "pac": pac_range,
    }
