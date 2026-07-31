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
    ingredient_from_nutrition_label,
    scale_recipe,
    seed_recipe,
    solve_recipe,
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


def test_solver_round_trips_seed_recipe() -> None:
    library = default_library()
    recipe = seed_recipe()
    metrics = calculate_recipe(recipe, library)

    solved = solve_recipe(
        recipe,
        library,
        Targets(
            total_mass=metrics.total_mass,
            fat_pct=metrics.fat_pct,
            msnf_pct=metrics.msnf_pct,
            pod=metrics.pod,
            pac=metrics.pac,
        ),
    )

    for expected, actual in zip(recipe[:5], solved[:5], strict=True):
        assert actual.ingredient_id == expected.ingredient_id
        assert actual.grams == pytest.approx(expected.grams, abs=1e-7)


@pytest.mark.parametrize("preset_id", BASE_PRESET_INFO)
def test_base_presets_are_balanced_solver_ready_reference_batches(preset_id: str) -> None:
    library = default_library()
    recipe = base_recipe(preset_id)
    metrics = calculate_recipe(recipe, library)

    assert metrics.total_mass == pytest.approx(1000.0)
    assert sum(line.free for line in recipe) == 5
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


def test_solver_rejects_wrong_number_of_free_rows() -> None:
    library = default_library()
    recipe = [
        RecipeLine(line.ingredient_id, line.grams, index < 4)
        for index, line in enumerate(seed_recipe())
    ]

    with pytest.raises(FormulationError, match="exactly five"):
        solve_recipe(recipe, library, Targets(1000, 13.5, 11.5, 112, 248))


def test_solver_reports_infeasible_targets_without_negative_output() -> None:
    library = default_library()

    with pytest.raises(FormulationError, match="require"):
        solve_recipe(
            seed_recipe(),
            library,
            Targets(
                total_mass=1000,
                fat_pct=2,
                msnf_pct=20,
                pod=20,
                pac=400,
            ),
        )


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
    assert ingredient.component("other_solids") == pytest.approx(12.0)
    assert ingredient.component("water") == pytest.approx(65.8)
    assert ingredient.accounted_mass == pytest.approx(100.0)


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
