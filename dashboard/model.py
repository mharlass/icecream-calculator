"""Pure-Python formulation engine for the ice cream dashboard.

The model contains no Shiny code. This keeps the formulation arithmetic independently
testable and compatible with Shinylive's browser-side Python runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
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

ADDED_SUGAR_COMPONENTS = {
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
    *ADDED_SUGAR_COMPONENTS,
    "maltodextrin_15de",
    "inulin",
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
    """Exactly determined targets for the five-variable inverse solver."""

    total_mass: float
    fat_pct: float
    msnf_pct: float
    pod: float
    pac: float


@dataclass(frozen=True)
class Metrics:
    """Computed formulation metrics, normalized to the current batch mass."""

    total_mass: float = 0.0
    fat_pct: float = 0.0
    msnf_pct: float = 0.0
    added_sugars_pct: float = 0.0
    nonfat_solids_pct: float = 0.0
    total_solids_pct: float = 0.0
    water_pct: float = 0.0
    gums_pct: float = 0.0
    pod: float = 0.0
    pac: float = 0.0
    pac_per_100g: float = 0.0
    absolute_pac: float = 0.0
    dextrose_share_pct: float = 0.0
    lactose_water_pct: float = 0.0
    component_grams: dict[str, float] = field(default_factory=dict)
    sugar_grams: dict[str, float] = field(default_factory=dict)


class FormulationError(ValueError):
    """Raised when an inverse formulation target cannot be solved safely."""


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
            "cocoa_powder",
            "Cocoa powder · approximate",
            "Flavor",
            {"fat": 22.0, "other_solids": 73.0, "water": 5.0},
            "Approximation only; replace with the package values for precise work.",
        ),
        Ingredient(
            "dark_chocolate_70",
            "Dark chocolate · 70% approximate",
            "Flavor",
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
        A new recipe list whose first five rows are available to the inverse solver.

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
    sugar_grams = {
        component: component_grams.get(component, 0.0)
        for component in ADDED_SUGAR_COMPONENTS
        if component_grams.get(component, 0.0) > 0
    }
    added_sugars_grams = sum(sugar_grams.values())
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
        added_sugars_pct=added_sugars_grams * scale,
        nonfat_solids_pct=nonfat_solids_grams * scale,
        total_solids_pct=(fat_grams + nonfat_solids_grams) * scale,
        water_pct=water_pct,
        gums_pct=gums_grams * scale,
        pod=pod_absolute * 1000.0 / total_mass,
        pac=pac,
        pac_per_100g=pac / 10.0,
        absolute_pac=pac / (water_pct / 100.0) if water_pct else 0.0,
        dextrose_share_pct=(
            100.0 * sugar_grams.get("dextrose", 0.0) / added_sugars_grams
            if added_sugars_grams
            else 0.0
        ),
        lactose_water_pct=(100.0 * lactose_grams / water_grams if water_grams else 0.0),
        component_grams=component_grams,
        sugar_grams=sugar_grams,
    )


def diagnose_recipe(metrics: Metrics, *, fat_cap: float = 15.0) -> list[str]:
    """Return plain-language safety and feasibility warnings."""

    warnings: list[str] = []
    if metrics.total_mass <= 0:
        return ["Add at least one ingredient with a positive quantity."]
    if metrics.fat_pct > fat_cap:
        warnings.append(f"Fat is {metrics.fat_pct:.1f}%, above your {fat_cap:.1f}% cap.")
    if metrics.lactose_water_pct > 10.0:
        warnings.append(
            "Estimated lactose exceeds 10% of the water phase; sandy lactose crystals "
            "become more likely."
        )
    if metrics.dextrose_share_pct > 50.0:
        warnings.append(
            "Dextrose exceeds 50% of the added-sugar blend, above Underbelly's suggested ceiling."
        )
    if not 35.0 <= metrics.total_solids_pct <= 45.0:
        warnings.append(
            f"Total solids are {metrics.total_solids_pct:.1f}%; keep them between 35% and 45%."
        )
    return warnings


def _solve_linear_system(matrix: list[list[float]], rhs: list[float]) -> list[float]:
    """Solve a square linear system with partial-pivot Gaussian elimination."""

    size = len(rhs)
    augmented = [row[:] + [rhs_value] for row, rhs_value in zip(matrix, rhs, strict=True)]
    for pivot_index in range(size):
        pivot_row = max(
            range(pivot_index, size),
            key=lambda row_index: abs(augmented[row_index][pivot_index]),
        )
        pivot = augmented[pivot_row][pivot_index]
        if abs(pivot) < 1e-10:
            raise FormulationError(
                "The five free ingredients do not span all five targets. Choose "
                "ingredients with distinct fat, MSNF, POD, and PAC contributions."
            )
        augmented[pivot_index], augmented[pivot_row] = (
            augmented[pivot_row],
            augmented[pivot_index],
        )
        augmented[pivot_index] = [value / pivot for value in augmented[pivot_index]]
        for row_index in range(size):
            if row_index == pivot_index:
                continue
            factor = augmented[row_index][pivot_index]
            augmented[row_index] = [
                value - factor * pivot_value
                for value, pivot_value in zip(
                    augmented[row_index],
                    augmented[pivot_index],
                    strict=True,
                )
            ]
    return [augmented[index][-1] for index in range(size)]


def solve_recipe(
    lines: list[RecipeLine],
    library: dict[str, Ingredient],
    targets: Targets,
) -> list[RecipeLine]:
    """Solve five free quantities against mass, fat, MSNF, POD, and PAC targets.

    Args:
        lines: Current formula. Exactly five rows must have ``free=True``.
        library: Ingredients keyed by stable ID.
        targets: Desired normalized formulation targets.

    Returns:
        A new list with the five free quantities replaced by solved values.

    Raises:
        FormulationError: If the system is not exactly determined, is singular,
            or needs a negative ingredient amount.
    """

    free_indices = [index for index, line in enumerate(lines) if line.free]
    if len(free_indices) != 5:
        raise FormulationError(f"Select exactly five free rows; {len(free_indices)} are selected.")
    if targets.total_mass <= 0:
        raise FormulationError(f"Target mass must be positive; got {targets.total_mass!r}.")

    locked_lines = [line for line in lines if not line.free]
    locked_metrics = _absolute_totals(locked_lines, library)
    target_absolute = [
        targets.total_mass,
        targets.total_mass * targets.fat_pct / 100.0,
        targets.total_mass * targets.msnf_pct / 100.0,
        targets.total_mass * targets.pod / 1000.0,
        targets.total_mass * targets.pac / 1000.0,
    ]
    rhs = [target - locked for target, locked in zip(target_absolute, locked_metrics, strict=True)]

    free_ingredients = [library[lines[index].ingredient_id] for index in free_indices]
    matrix = [
        [1.0 for _ in free_ingredients],
        [ingredient.component("fat") / 100.0 for ingredient in free_ingredients],
        [ingredient.component("msnf") / 100.0 for ingredient in free_ingredients],
        [ingredient_pod_coefficient(ingredient) for ingredient in free_ingredients],
        [ingredient_pac_coefficient(ingredient) for ingredient in free_ingredients],
    ]
    solution = _solve_linear_system(matrix, rhs)
    negative = [
        (free_ingredients[index].name, value)
        for index, value in enumerate(solution)
        if value < -1e-6
    ]
    if negative:
        name, value = min(negative, key=lambda item: item[1])
        raise FormulationError(
            f"Those targets require {value:.1f} g of {name}. Relax a target or "
            "choose a different set of free ingredients."
        )

    result = lines[:]
    for index, solved_grams in zip(free_indices, solution, strict=True):
        result[index] = RecipeLine(
            ingredient_id=result[index].ingredient_id,
            grams=max(0.0, solved_grams),
            free=True,
        )
    return result


def _absolute_totals(
    lines: list[RecipeLine],
    library: dict[str, Ingredient],
) -> list[float]:
    """Return mass, fat, MSNF, POD, and PAC contributions without normalization."""

    mass = sum(line.grams for line in lines)
    fat = sum(line.grams * library[line.ingredient_id].component("fat") / 100.0 for line in lines)
    msnf = sum(line.grams * library[line.ingredient_id].component("msnf") / 100.0 for line in lines)
    pod = sum(
        line.grams * ingredient_pod_coefficient(library[line.ingredient_id]) for line in lines
    )
    pac = sum(
        line.grams * ingredient_pac_coefficient(library[line.ingredient_id]) for line in lines
    )
    return [mass, fat, msnf, pod, pac]


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

    other_solids = carbohydrate - sugars + protein + fibre
    declared_without_water = fat + sugars + other_solids + salt
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
        category="Custom",
        components={
            "fat": fat,
            sugar_component: sugars,
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


def ingredient_from_composition(
    *,
    ingredient_id: str,
    name: str,
    fat: float,
    msnf: float,
    soluble_component: str,
    soluble_amount: float,
    other_solids: float,
    salt: float,
    alcohol: float,
    gums: float,
    water: float,
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

    declared_without_water = fat + msnf + soluble_amount + other_solids + salt + alcohol + gums
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
        category="Custom",
        components={
            "fat": fat,
            "msnf": msnf,
            soluble_component: soluble_amount,
            "other_solids": resolved_other_solids,
            "salt": salt,
            "alcohol": alcohol,
            "gums": gums,
            "water": resolved_water,
        },
        note="Direct component composition supplied by the user.",
        custom=True,
    )


def target_ranges(target_set: str, *, fat_cap: float = 15.0) -> dict[str, tuple[float, float]]:
    """Return display target ranges for the active production method."""

    pac_range = (245.0, 255.0) if target_set == "Creami / Pacojet" else (220.0, 230.0)
    return {
        "fat_pct": (12.0, fat_cap),
        "msnf_pct": (10.0, 12.0),
        "added_sugars_pct": (11.0, 14.0),
        "nonfat_solids_pct": (22.0, 25.0),
        "total_solids_pct": (37.0, 42.0),
        "water_pct": (58.0, 63.0),
        "gums_pct": (0.15, 0.20),
        "pod": (110.0, 120.0),
        "pac": pac_range,
    }
