"""Verification tests for the ice cream formulation engine."""

from __future__ import annotations

import pytest

from dashboard.model import (
    BASE_PRESET_INFO,
    FormulationError,
    RecipeLine,
    Targets,
    base_recipe,
    calculate_recipe,
    default_library,
    diagnose_recipe,
    ingredient_from_fruit_composition,
    ingredient_from_nutrition_label,
    optimize_recipe,
    scale_recipe,
    seed_recipe,
    target_ranges,
)


def test_seed_recipe_matches_balanced_reference() -> None:
    library = default_library()
    metrics = calculate_recipe(seed_recipe(), library)

    assert metrics.total_mass == pytest.approx(1000.0)
    assert metrics.fat_pct == pytest.approx(13.496)
    assert metrics.msnf_pct == pytest.approx(11.5288625)
    assert metrics.added_sugars_pct == pytest.approx(11.5)
    assert metrics.total_solids_pct == pytest.approx(39.0248625)
    assert metrics.water_pct == pytest.approx(60.9751375)
    assert metrics.gums_pct == pytest.approx(0.18)
    assert metrics.pod == pytest.approx(111.568955875)
    assert metrics.pac == pytest.approx(248.4558575)
    assert metrics.dextrose_share_pct == pytest.approx(43.47826087)
    assert metrics.lactose_water_pct < 10.0
    assert diagnose_recipe(metrics, fat_cap=15.0) == []


def test_optimizer_round_trips_seed_recipe() -> None:
    library = default_library()
    recipe = seed_recipe()
    metrics = calculate_recipe(recipe, library)

    optimized = optimize_recipe(
        recipe,
        library,
        Targets(
            total_mass=metrics.total_mass,
            fat_pct=metrics.fat_pct,
            msnf_pct=metrics.msnf_pct,
            total_solids_pct=metrics.total_solids_pct,
            pod=metrics.pod,
            pac=metrics.pac,
        ),
    )

    assert optimized.target_errors == pytest.approx(
        {
            "fat_pct": 0.0,
            "msnf_pct": 0.0,
            "total_solids_pct": 0.0,
            "pod": 0.0,
            "pac": 0.0,
        },
        abs=1e-9,
    )
    for expected, actual in zip(recipe[:5], optimized.lines[:5], strict=True):
        assert actual.ingredient_id == expected.ingredient_id
        assert actual.grams == pytest.approx(expected.grams, abs=1e-7)


@pytest.mark.parametrize("preset_id", BASE_PRESET_INFO)
def test_base_presets_are_balanced_optimizer_ready_reference_batches(preset_id: str) -> None:
    library = default_library()
    recipe = base_recipe(preset_id)
    metrics = calculate_recipe(recipe, library)

    assert metrics.total_mass == pytest.approx(1000.0)
    assert sum(line.free for line in recipe) == 5
    if preset_id == "strawberry_sorbet":
        assert metrics.fat_pct == pytest.approx(0.165)
        assert metrics.msnf_pct == 0
        assert metrics.total_solids_pct == pytest.approx(26.8)
        assert metrics.pod == pytest.approx(130.765)
        assert metrics.pac == pytest.approx(296.355)
        assert (
            diagnose_recipe(
                metrics,
                fat_cap=18.0,
                target_set="Fruit sorbet · experimental",
            )
            == []
        )
    else:
        assert 12.0 <= metrics.fat_pct <= 15.0
        assert 105.0 <= metrics.pod <= 120.0
        assert 245.0 <= metrics.pac <= 255.0
        assert diagnose_recipe(metrics, fat_cap=18.0) == []


def test_custard_presets_include_the_selected_egg_form() -> None:
    yolk_ids = {line.ingredient_id for line in base_recipe("yolk_custard")}
    whole_egg_ids = {line.ingredient_id for line in base_recipe("whole_egg_custard")}

    assert "egg_yolk" in yolk_ids
    assert "whole_egg" not in yolk_ids
    assert "whole_egg" in whole_egg_ids
    assert "egg_yolk" not in whole_egg_ids


def test_additive_library_includes_practical_stabilizer_and_emulsifier_options() -> None:
    library = default_library()

    expected_ids = {
        "cmc",
        "guar",
        "lambda_carrageenan",
        "xanthan",
        "gelatin",
        "collagen_peptides",
        "locust_bean_gum",
        "tara_gum",
        "sodium_alginate",
        "kappa_carrageenan",
        "soy_lecithin",
        "sunflower_lecithin",
        "mono_diglycerides",
        "polysorbate_80",
    }

    assert expected_ids <= library.keys()
    assert library["collagen_peptides"].component("gums") == 0
    assert library["collagen_peptides"].component("other_solids") == 100
    assert library["gelatin"].component("gums") == 100


def test_library_includes_sourced_fruit_and_chocolate_components() -> None:
    library = default_library()

    strawberry = library["strawberry_puree"]
    assert strawberry.accounted_mass == pytest.approx(100.0)
    assert strawberry.component("dextrose") == pytest.approx(2.24)
    assert strawberry.component("fructose") == pytest.approx(2.62)
    assert strawberry.component("fiber") == 0
    assert "no fiber value" in strawberry.note

    cocoa = library["cocoa_powder"]
    assert cocoa.accounted_mass == pytest.approx(100.0)
    assert cocoa.component("fiber") == pytest.approx(37.0)


def test_base_recipe_rejects_unknown_preset() -> None:
    with pytest.raises(ValueError, match="Unknown base preset"):
        base_recipe("frozen_yogurt")


def test_scaling_preserves_normalized_metrics() -> None:
    library = default_library()
    original = calculate_recipe(seed_recipe(), library)
    scaled_recipe = scale_recipe(seed_recipe(), 750.0)
    scaled = calculate_recipe(scaled_recipe, library)

    assert scaled.total_mass == pytest.approx(750.0)
    assert scaled.fat_pct == pytest.approx(original.fat_pct)
    assert scaled.msnf_pct == pytest.approx(original.msnf_pct)
    assert scaled.pod == pytest.approx(original.pod)
    assert scaled.pac == pytest.approx(original.pac)


def test_optimizer_accepts_any_positive_number_of_adjustable_rows() -> None:
    library = default_library()
    recipe = [
        RecipeLine(line.ingredient_id, line.grams, index in {0, 3, 4})
        for index, line in enumerate(seed_recipe())
    ]
    current = calculate_recipe(recipe, library)

    optimized = optimize_recipe(
        recipe,
        library,
        Targets(
            total_mass=1000,
            pod=current.pod + 5,
            pac=current.pac + 10,
        ),
    )

    assert sum(line.free for line in optimized.lines) == 3
    assert calculate_recipe(optimized.lines, library).total_mass == pytest.approx(1000)
    assert all(line.grams >= 0 for line in optimized.lines)


def test_optimizer_returns_closest_nonnegative_formula_for_infeasible_targets() -> None:
    library = default_library()

    optimized = optimize_recipe(
        seed_recipe(),
        library,
        Targets(
            total_mass=1000,
            fat_pct=2,
            msnf_pct=20,
            total_solids_pct=25,
            pod=20,
            pac=400,
        ),
    )

    assert calculate_recipe(optimized.lines, library).total_mass == pytest.approx(1000)
    assert all(line.grams >= 0 for line in optimized.lines)
    assert any(abs(error) > 0.5 for error in optimized.target_errors.values())


def test_optimizer_rejects_empty_target_selection() -> None:
    with pytest.raises(FormulationError, match="at least one composition target"):
        optimize_recipe(seed_recipe(), default_library(), Targets(total_mass=1000))


def test_optimizer_rejects_recipe_without_adjustable_rows() -> None:
    recipe = [RecipeLine(line.ingredient_id, line.grams) for line in seed_recipe()]

    with pytest.raises(FormulationError, match="at least one ingredient row"):
        optimize_recipe(
            recipe,
            default_library(),
            Targets(total_mass=1000, pod=112),
        )


def test_optimizer_balances_sorbet_without_dairy_targets() -> None:
    library = default_library()
    optimized = optimize_recipe(
        base_recipe("strawberry_sorbet"),
        library,
        Targets(
            total_mass=1000,
            total_solids_pct=29,
            pod=170,
            pac=320,
        ),
    )
    metrics = calculate_recipe(optimized.lines, library)

    assert metrics.total_mass == pytest.approx(1000)
    assert metrics.fat_pct < 0.2
    assert metrics.msnf_pct == 0
    assert all(line.grams >= 0 for line in optimized.lines)
    assert abs(optimized.target_errors["total_solids_pct"]) < 2
    assert abs(optimized.target_errors["pod"]) < 3
    assert abs(optimized.target_errors["pac"]) < 1


def test_custom_nutrition_label_maps_sugars_and_infers_water() -> None:
    ingredient = ingredient_from_nutrition_label(
        ingredient_id="custom_1",
        name="Sweetened dairy",
        fat=8.0,
        carbohydrate=20.0,
        sugars=14.0,
        protein=5.0,
        fibre=1.0,
        salt=0.2,
        water=0.0,
        sugar_component="dextrose",
    )

    assert ingredient.component("dextrose") == pytest.approx(14.0)
    assert ingredient.component("fiber") == pytest.approx(1.0)
    assert ingredient.component("other_solids") == pytest.approx(11.0)
    assert ingredient.component("water") == pytest.approx(65.8)
    assert ingredient.accounted_mass == pytest.approx(100.0)


def test_fruit_composition_preserves_sugar_species_and_fiber() -> None:
    ingredient = ingredient_from_fruit_composition(
        ingredient_id="custom_fruit",
        name="Measured mango purée",
        fat=0.4,
        water=82.0,
        sucrose=7.0,
        glucose=2.0,
        fructose=4.5,
        fiber=1.7,
        other_solids=2.4,
        brix=16.0,
    )

    assert ingredient.category == "Fruit & purée"
    assert ingredient.component("sucrose") == pytest.approx(7.0)
    assert ingredient.component("dextrose") == pytest.approx(2.0)
    assert ingredient.component("fructose") == pytest.approx(4.5)
    assert ingredient.component("fiber") == pytest.approx(1.7)
    assert ingredient.accounted_mass == pytest.approx(100.0)
    assert "16 °Bx" in ingredient.note


def test_sorbet_target_ranges_do_not_treat_dairy_metrics_as_targets() -> None:
    ranges = target_ranges("Fruit sorbet · experimental")

    assert ranges["fat_pct"] is None
    assert ranges["msnf_pct"] is None
    assert ranges["total_solids_pct"] == (25.0, 33.0)
    assert ranges["pod"] == (140.0, 200.0)
    assert ranges["pac"] == (300.0, 340.0)


def test_custom_nutrition_label_rejects_impossible_values() -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        ingredient_from_nutrition_label(
            ingredient_id="custom_1",
            name="Bad label",
            fat=1.0,
            carbohydrate=5.0,
            sugars=8.0,
            protein=1.0,
            fibre=0.0,
            salt=0.0,
            water=0.0,
        )
