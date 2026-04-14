import logging

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

from eu_forest_biomass_tradeoff_explorer.allocation import (
    FOOD_LAND_POLICY_LABEL,
    build_regional_policy_options,
    select_regional_policy_priorities,
)
from eu_forest_biomass_tradeoff_explorer.config import DEFAULT_MODEL_PARAMETERS
from eu_forest_biomass_tradeoff_explorer.model import (
    _scenario_volumes,
    best_scenario_by_country,
    build_baseline_metrics,
    evaluate_scenarios,
)
from eu_forest_biomass_tradeoff_explorer.optimization import (
    constraint_debug_lines,
    optimize_regional_policy_portfolio,
    validate_constraint_metrics,
)
from eu_forest_biomass_tradeoff_explorer.plotting import _optimized_constraint_plot_metrics
from eu_forest_biomass_tradeoff_explorer.regional import build_nuts2_screening_dataset
from eu_forest_biomass_tradeoff_explorer.sensitivity import run_sensitivity_analysis


def _sample_inputs() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "country": "Exampleland",
                "country_code": "EX",
                "iso3_code": "EXP",
                "forest_area_kha": 100.0,
                "forest_carbon_stock_mt_c": 10.0,
                "naturally_regenerating_forest_kha": 70.0,
                "planted_forest_kha": 20.0,
                "primary_forest_kha": 5.0,
                "roundwood_m3": 1_000.0,
                "industrial_roundwood_m3": 700.0,
                "wood_fuel_m3": 300.0,
                "sawnwood_m3": 350.0,
                "wood_pellets_t": 50.0,
                "selected_food_crop_area_kha": 40.0,
                "selected_food_production_kt": 180.0,
                "food_production_intensity_index": 0.9,
            },
            {
                "country": "Timberia",
                "country_code": "TI",
                "iso3_code": "TIM",
                "forest_area_kha": 120.0,
                "forest_carbon_stock_mt_c": 8.0,
                "naturally_regenerating_forest_kha": 60.0,
                "planted_forest_kha": 40.0,
                "primary_forest_kha": 1.0,
                "roundwood_m3": 1_500.0,
                "industrial_roundwood_m3": 900.0,
                "wood_fuel_m3": 600.0,
                "sawnwood_m3": 360.0,
                "wood_pellets_t": 70.0,
                "selected_food_crop_area_kha": 55.0,
                "selected_food_production_kt": 320.0,
                "food_production_intensity_index": 1.2,
            },
        ]
    )


def test_conservation_reduces_harvest() -> None:
    row = _sample_inputs().iloc[0]
    scenario = _scenario_volumes(row, "conservation_priority")
    assert scenario["harvest_total_m3"] < row["industrial_roundwood_m3"] + row["wood_fuel_m3"]
    assert scenario["wood_fuel_m3"] <= row["wood_fuel_m3"]


def test_material_cascade_preserves_total_harvest() -> None:
    row = _sample_inputs().iloc[0]
    scenario = _scenario_volumes(row, "material_cascade")
    assert scenario["harvest_total_m3"] == row["industrial_roundwood_m3"] + row["wood_fuel_m3"]
    assert scenario["industrial_roundwood_m3"] > row["industrial_roundwood_m3"]
    assert scenario["wood_fuel_m3"] < row["wood_fuel_m3"]


def test_bioenergy_push_increases_harvest() -> None:
    row = _sample_inputs().iloc[0]
    scenario = _scenario_volumes(row, "bioenergy_push")
    assert scenario["harvest_total_m3"] > row["industrial_roundwood_m3"] + row["wood_fuel_m3"]
    assert scenario["wood_fuel_m3"] > row["wood_fuel_m3"]


def test_scenario_evaluation_has_one_row_per_country_and_scenario() -> None:
    baseline = build_baseline_metrics(_sample_inputs())
    results = evaluate_scenarios(baseline)
    assert len(results) == len(baseline) * 4
    assert set(results["scenario"]) == {"baseline", "conservation_priority", "material_cascade", "bioenergy_push"}


def test_higher_opportunity_cost_strengthens_conservation_signal() -> None:
    low_cost = DEFAULT_MODEL_PARAMETERS.__class__(**{**DEFAULT_MODEL_PARAMETERS.__dict__, "base_forest_carbon_opportunity_cost_tco2e_per_m3": 0.35})
    high_cost = DEFAULT_MODEL_PARAMETERS.__class__(**{**DEFAULT_MODEL_PARAMETERS.__dict__, "base_forest_carbon_opportunity_cost_tco2e_per_m3": 0.85})
    baseline_low = build_baseline_metrics(_sample_inputs(), parameters=low_cost)
    baseline_high = build_baseline_metrics(_sample_inputs(), parameters=high_cost)
    results_low = evaluate_scenarios(baseline_low, parameters=low_cost)
    results_high = evaluate_scenarios(baseline_high, parameters=high_cost)
    conservation_low = results_low.loc[results_low["scenario"] == "conservation_priority", "net_climate_benefit_tco2e"].sum()
    conservation_high = results_high.loc[results_high["scenario"] == "conservation_priority", "net_climate_benefit_tco2e"].sum()
    assert conservation_high > conservation_low


def test_best_scenario_excludes_zero_baseline_activity() -> None:
    inputs = _sample_inputs().iloc[[0]].copy()
    inputs.loc[:, "industrial_roundwood_m3"] = 0.0
    inputs.loc[:, "wood_fuel_m3"] = 0.0
    baseline = build_baseline_metrics(inputs)
    results = evaluate_scenarios(baseline)
    selected = best_scenario_by_country(results)
    assert selected.empty


def test_sensitivity_analysis_returns_probability_distribution() -> None:
    outputs = run_sensitivity_analysis(_sample_inputs(), sample_size=8, seed=7)
    robustness = outputs["country_robustness"]
    probability_sums = robustness.groupby("country")["share_best"].sum()
    assert len(outputs["parameter_draws"]) == 8
    assert all(abs(value - 1.0) < 1e-9 for value in probability_sums)


def test_nuts2_screening_dataset_allocates_country_values_by_woodland_share(monkeypatch) -> None:
    def fake_geometries() -> gpd.GeoDataFrame:
        return gpd.GeoDataFrame(
            {
                "nuts2_id": ["EX01", "EX02"],
                "country_code": ["EX", "EX"],
                "nuts2_name": ["North Example", "South Example"],
                "geometry": [
                    Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                    Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
                ],
            },
            geometry="geometry",
            crs="EPSG:4326",
        )

    def fake_landcover() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "nuts2_id": ["EX01", "EX02"],
                "total_area_km2": [100.0, 100.0],
                "woodland_area_km2": [60.0, 40.0],
                "broadleaved_woodland_km2": [20.0, 10.0],
                "coniferous_woodland_km2": [30.0, 20.0],
                "mixed_woodland_km2": [10.0, 10.0],
                "cropland_area_km2": [20.0, 50.0],
                "grassland_area_km2": [10.0, 30.0],
                "agricultural_land_area_km2": [30.0, 80.0],
                "feed_land_area_km2": [15.0, 50.0],
                "woodland_share_of_land": [0.6, 0.4],
                "cropland_share_of_land": [0.2, 0.5],
                "grassland_share_of_land": [0.1, 0.3],
                "agricultural_land_share_of_land": [0.3, 0.8],
                "broadleaved_share_of_woodland": [20 / 60, 10 / 40],
                "coniferous_share_of_woodland": [30 / 60, 20 / 40],
                "mixed_share_of_woodland": [10 / 60, 10 / 40],
                "feed_land_share_of_agricultural_land": [0.5, 0.625],
                "permanent_crop_share_of_agricultural_land": [0.05, 0.15],
            }
        )

    monkeypatch.setattr("eu_forest_biomass_tradeoff_explorer.regional.load_nuts2_geometries", fake_geometries)
    monkeypatch.setattr("eu_forest_biomass_tradeoff_explorer.regional.load_nuts2_landcover_context", fake_landcover)

    baseline_metrics = pd.DataFrame(
        [
            {
                "country": "Exampleland",
                "country_code": "EX",
                "forest_area_ha": 10_000.0,
                "forest_carbon_stock_mtco2e": 5.0,
                "harvest_total_m3": 2_000.0,
                "carbon_stock_density_tco2e_per_ha": 500.0,
                "harvest_intensity_m3_per_ha": 0.2,
                "biodiversity_pressure_proxy": 0.1,
            }
        ]
    )
    best_scenarios = pd.DataFrame(
        [
            {
                "country": "Exampleland",
                "country_code": "EX",
                "scenario": "material_cascade",
                "scenario_label": "Material Cascade",
                "net_climate_benefit_tco2e": 1_000.0,
                "carbon_value_eur": 100_000.0,
                "net_climate_benefit_tco2e_per_ha": 0.1,
                "carbon_value_eur_per_ha": 10.0,
            }
        ]
    )
    country_modal_scenario = pd.DataFrame(
        [
            {
                "country": "Exampleland",
                "country_code": "EX",
                "iso3_code": "EXP",
                "scenario": "material_cascade",
                "scenario_label": "Material Cascade",
                "share_best": 0.75,
                "runner_up_scenario_label": "Conservation Priority",
                "robustness_margin": 0.5,
            }
        ]
    )

    result = build_nuts2_screening_dataset(
        baseline_metrics=baseline_metrics,
        best_scenarios=best_scenarios,
        country_modal_scenario=country_modal_scenario,
    )
    result = result.sort_values("nuts2_id").reset_index(drop=True)
    assert result.loc[0, "estimated_best_scenario_benefit_tco2e"] == 600.0
    assert result.loc[1, "estimated_best_scenario_benefit_tco2e"] == 400.0
    assert result.loc[0, "screening_priority_score"] > result.loc[1, "screening_priority_score"]
    assert set(result["is_forest_only"]) == {True}
    assert set(result["includes_food_policy"]) == {False}


def test_nuts2_screening_dataset_can_override_sweden_with_empirical_inputs(monkeypatch) -> None:
    def fake_geometries() -> gpd.GeoDataFrame:
        return gpd.GeoDataFrame(
            {
                "nuts2_id": ["SE11"],
                "country_code": ["SE"],
                "nuts2_name": ["Stockholm"],
                "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
            },
            geometry="geometry",
            crs="EPSG:4326",
        )

    def fake_landcover() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "nuts2_id": ["SE11"],
                "total_area_km2": [100.0],
                "woodland_area_km2": [30.0],
                "broadleaved_woodland_km2": [5.0],
                "coniferous_woodland_km2": [20.0],
                "mixed_woodland_km2": [5.0],
                "cropland_area_km2": [10.0],
                "grassland_area_km2": [5.0],
                "agricultural_land_area_km2": [15.0],
                "feed_land_area_km2": [6.0],
                "woodland_share_of_land": [0.30],
                "cropland_share_of_land": [0.10],
                "grassland_share_of_land": [0.05],
                "agricultural_land_share_of_land": [0.15],
                "broadleaved_share_of_woodland": [5 / 30],
                "coniferous_share_of_woodland": [20 / 30],
                "mixed_share_of_woodland": [5 / 30],
                "feed_land_share_of_agricultural_land": [0.4],
                "permanent_crop_share_of_agricultural_land": [0.05],
            }
        )

    monkeypatch.setattr("eu_forest_biomass_tradeoff_explorer.regional.load_nuts2_geometries", fake_geometries)
    monkeypatch.setattr("eu_forest_biomass_tradeoff_explorer.regional.load_nuts2_landcover_context", fake_landcover)

    baseline_metrics = pd.DataFrame(
        [
            {
                "country": "Sweden",
                "country_code": "SE",
                "forest_area_ha": 1_000.0,
                "forest_carbon_stock_mtco2e": 2.0,
                "harvest_total_m3": 80.0,
                "carbon_stock_density_tco2e_per_ha": 2_000.0,
                "harvest_intensity_m3_per_ha": 0.08,
                "biodiversity_pressure_proxy": 0.03,
            }
        ]
    )
    best_scenarios = pd.DataFrame(
        [
            {
                "country": "Sweden",
                "country_code": "SE",
                "scenario": "material_cascade",
                "scenario_label": "Material Cascade",
                "net_climate_benefit_tco2e": 100.0,
                "carbon_value_eur": 10_000.0,
                "net_climate_benefit_tco2e_per_ha": 0.1,
                "carbon_value_eur_per_ha": 10.0,
            }
        ]
    )
    country_modal_scenario = pd.DataFrame(
        [
            {
                "country": "Sweden",
                "country_code": "SE",
                "iso3_code": "SWE",
                "scenario": "material_cascade",
                "scenario_label": "Material Cascade",
                "share_best": 0.8,
                "runner_up_scenario_label": "Conservation Priority",
                "robustness_margin": 0.2,
            }
        ]
    )
    sweden_empirical_case = {
        "baseline_metrics": pd.DataFrame(
            [
                {
                    "nuts2_id": "SE11",
                    "nuts2_name": "Stockholm",
                    "forest_area_ha": 1_500.0,
                    "forest_carbon_stock_mtco2e": 3.4,
                    "harvest_total_m3": 120.0,
                    "carbon_stock_density_tco2e_per_ha": 2_266.7,
                    "harvest_intensity_m3_per_ha": 0.08,
                    "biodiversity_pressure_proxy": 0.02,
                }
            ]
        ),
        "best_scenarios": pd.DataFrame(
            [
                {
                    "nuts2_id": "SE11",
                    "nuts2_name": "Stockholm",
                    "scenario": "conservation_priority",
                    "scenario_label": "Conservation Priority",
                    "net_climate_benefit_tco2e": 240.0,
                    "carbon_value_eur": 24_000.0,
                    "net_climate_benefit_tco2e_per_ha": 0.16,
                    "carbon_value_eur_per_ha": 16.0,
                }
            ]
        ),
    }

    result = build_nuts2_screening_dataset(
        baseline_metrics=baseline_metrics,
        best_scenarios=best_scenarios,
        country_modal_scenario=country_modal_scenario,
        sweden_empirical_case=sweden_empirical_case,
    )

    row = result.iloc[0]
    assert row["forest_data_source"] == "SLU NFI county aggregation"
    assert row["estimated_forest_area_ha"] == 1_500.0
    assert row["estimated_best_scenario_benefit_tco2e"] == 240.0
    assert row["scenario_label"] == "Conservation Priority"


def test_nuts2_screening_dataset_warns_when_regions_are_dropped(monkeypatch, caplog) -> None:
    def fake_geometries() -> gpd.GeoDataFrame:
        return gpd.GeoDataFrame(
            {
                "nuts2_id": ["EX01", "EX02"],
                "country_code": ["EX", "EX"],
                "nuts2_name": ["North Example", "South Example"],
                "geometry": [
                    Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                    Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
                ],
            },
            geometry="geometry",
            crs="EPSG:4326",
        )

    def fake_landcover() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "nuts2_id": ["EX01"],
                "total_area_km2": [100.0],
                "woodland_area_km2": [60.0],
                "broadleaved_woodland_km2": [20.0],
                "coniferous_woodland_km2": [30.0],
                "mixed_woodland_km2": [10.0],
                "cropland_area_km2": [20.0],
                "grassland_area_km2": [10.0],
                "agricultural_land_area_km2": [30.0],
                "feed_land_area_km2": [15.0],
                "woodland_share_of_land": [0.6],
                "cropland_share_of_land": [0.2],
                "grassland_share_of_land": [0.1],
                "agricultural_land_share_of_land": [0.3],
                "broadleaved_share_of_woodland": [20 / 60],
                "coniferous_share_of_woodland": [30 / 60],
                "mixed_share_of_woodland": [10 / 60],
                "feed_land_share_of_agricultural_land": [0.5],
                "permanent_crop_share_of_agricultural_land": [0.05],
            }
        )

    monkeypatch.setattr("eu_forest_biomass_tradeoff_explorer.regional.load_nuts2_geometries", fake_geometries)
    monkeypatch.setattr("eu_forest_biomass_tradeoff_explorer.regional.load_nuts2_landcover_context", fake_landcover)

    baseline_metrics = pd.DataFrame(
        [
            {
                "country": "Exampleland",
                "country_code": "EX",
                "forest_area_ha": 10_000.0,
                "forest_carbon_stock_mtco2e": 5.0,
                "harvest_total_m3": 2_000.0,
                "carbon_stock_density_tco2e_per_ha": 500.0,
                "harvest_intensity_m3_per_ha": 0.2,
                "biodiversity_pressure_proxy": 0.1,
            }
        ]
    )
    best_scenarios = pd.DataFrame(
        [
            {
                "country": "Exampleland",
                "country_code": "EX",
                "scenario": "material_cascade",
                "scenario_label": "Material Cascade",
                "net_climate_benefit_tco2e": 1_000.0,
                "carbon_value_eur": 100_000.0,
                "net_climate_benefit_tco2e_per_ha": 0.1,
                "carbon_value_eur_per_ha": 10.0,
            }
        ]
    )
    country_modal_scenario = pd.DataFrame(
        [
            {
                "country": "Exampleland",
                "country_code": "EX",
                "iso3_code": "EXP",
                "scenario": "material_cascade",
                "scenario_label": "Material Cascade",
                "share_best": 0.75,
                "runner_up_scenario_label": "Conservation Priority",
                "robustness_margin": 0.5,
            }
        ]
    )

    with caplog.at_level(logging.WARNING):
        result = build_nuts2_screening_dataset(
            baseline_metrics=baseline_metrics,
            best_scenarios=best_scenarios,
            country_modal_scenario=country_modal_scenario,
        )

    assert len(result) == 1
    assert "Dropping 1 NUTS-2 regions" in caplog.text


def test_integrated_policy_can_switch_from_forest_to_food_land_when_agricultural_pressure_is_high() -> None:
    nuts2_screening = pd.DataFrame(
        [
            {
                "nuts2_id": "EX01",
                "nuts2_name": "Forest North",
                "country": "Exampleland",
                "country_code": "EX",
                "total_area_km2": 100.0,
                "woodland_area_km2": 60.0,
                "cropland_area_km2": 20.0,
                "grassland_area_km2": 10.0,
                "agricultural_land_area_km2": 30.0,
                "feed_land_area_km2": 15.0,
                "woodland_share_of_land": 0.60,
                "cropland_share_of_land": 0.20,
                "grassland_share_of_land": 0.10,
                "agricultural_land_share_of_land": 0.30,
                "feed_land_share_of_agricultural_land": 0.50,
                "permanent_crop_share_of_agricultural_land": 0.05,
                "share_of_country_woodland": 0.92,
                "modal_scenario_share_best": 0.90,
                "forest_area_ha": 10_000.0,
                "harvest_total_m3": 1_000.0,
                "selected_food_crop_area_kha": 35.0,
                "selected_food_production_kt": 120.0,
                "food_production_intensity_index": 0.8,
            },
            {
                "nuts2_id": "EX02",
                "nuts2_name": "Agri South",
                "country": "Exampleland",
                "country_code": "EX",
                "total_area_km2": 100.0,
                "woodland_area_km2": 10.0,
                "cropland_area_km2": 55.0,
                "grassland_area_km2": 25.0,
                "agricultural_land_area_km2": 80.0,
                "feed_land_area_km2": 60.0,
                "woodland_share_of_land": 0.10,
                "cropland_share_of_land": 0.55,
                "grassland_share_of_land": 0.25,
                "agricultural_land_share_of_land": 0.80,
                "feed_land_share_of_agricultural_land": 0.75,
                "permanent_crop_share_of_agricultural_land": 0.10,
                "share_of_country_woodland": 0.08,
                "modal_scenario_share_best": 0.90,
                "forest_area_ha": 10_000.0,
                "harvest_total_m3": 1_000.0,
                "selected_food_crop_area_kha": 35.0,
                "selected_food_production_kt": 120.0,
                "food_production_intensity_index": 1.5,
            },
        ]
    )
    scenario_results = pd.DataFrame(
        [
            {
                "country": "Exampleland",
                "country_code": "EX",
                "scenario": "conservation_priority",
                "scenario_label": "Conservation Priority",
                "scenario_description": "Cut harvest.",
                "net_climate_benefit_tco2e": 1_500.0,
                "carbon_value_eur": 150_000.0,
                "delta_biodiversity_pressure_proxy": -0.2,
                "changed_harvest_m3": 500.0,
                "harvest_total_m3": 850.0,
            },
            {
                "country": "Exampleland",
                "country_code": "EX",
                "scenario": "material_cascade",
                "scenario_label": "Material Cascade",
                "scenario_description": "Shift to materials.",
                "net_climate_benefit_tco2e": 2_000.0,
                "carbon_value_eur": 200_000.0,
                "delta_biodiversity_pressure_proxy": 0.0,
                "changed_harvest_m3": 400.0,
                "harvest_total_m3": 1_000.0,
            },
            {
                "country": "Exampleland",
                "country_code": "EX",
                "scenario": "bioenergy_push",
                "scenario_label": "Bioenergy Push",
                "scenario_description": "Increase harvest.",
                "net_climate_benefit_tco2e": -500.0,
                "carbon_value_eur": -50_000.0,
                "delta_biodiversity_pressure_proxy": 0.2,
                "changed_harvest_m3": 600.0,
                "harvest_total_m3": 1_150.0,
            },
        ]
    )

    policy_options = build_regional_policy_options(nuts2_screening, scenario_results)
    selected = select_regional_policy_priorities(policy_options)
    selected = selected.set_index("nuts2_id")

    assert selected.loc["EX01", "selected_policy_label"] == "Material Cascade"
    assert selected.loc["EX02", "selected_policy_label"] == FOOD_LAND_POLICY_LABEL
    assert selected.loc["EX02", "switch_from_best_forest"]
    assert selected.loc["EX02", "includes_food_policy"]
    assert not selected.loc["EX02", "is_forest_only"]
    assert selected.loc["EX02", "selected_policy_value_eur_per_land_ha"] > selected.loc["EX02", "best_forest_policy_value_eur_per_land_ha"]


def test_optimization_enforces_biomass_and_food_constraints() -> None:
    nuts2_screening = pd.DataFrame(
        [
            {
                "nuts2_id": "EX01",
                "nuts2_name": "Forest North",
                "country": "Exampleland",
                "country_code": "EX",
                "total_area_km2": 100.0,
                "woodland_area_km2": 70.0,
                "cropland_area_km2": 12.0,
                "grassland_area_km2": 8.0,
                "agricultural_land_area_km2": 20.0,
                "feed_land_area_km2": 8.0,
                "woodland_share_of_land": 0.70,
                "cropland_share_of_land": 0.12,
                "grassland_share_of_land": 0.08,
                "agricultural_land_share_of_land": 0.20,
                "feed_land_share_of_agricultural_land": 0.40,
                "permanent_crop_share_of_agricultural_land": 0.05,
                "share_of_country_woodland": 0.50,
                "modal_scenario_share_best": 0.85,
                "forest_area_ha": 20_000.0,
                "harvest_total_m3": 1_000.0,
                "selected_food_crop_area_kha": 60.0,
                "selected_food_production_kt": 250.0,
                "food_production_intensity_index": 0.9,
            },
            {
                "nuts2_id": "EX02",
                "nuts2_name": "Agri South",
                "country": "Exampleland",
                "country_code": "EX",
                "total_area_km2": 100.0,
                "woodland_area_km2": 30.0,
                "cropland_area_km2": 55.0,
                "grassland_area_km2": 25.0,
                "agricultural_land_area_km2": 80.0,
                "feed_land_area_km2": 55.0,
                "woodland_share_of_land": 0.30,
                "cropland_share_of_land": 0.55,
                "grassland_share_of_land": 0.25,
                "agricultural_land_share_of_land": 0.80,
                "feed_land_share_of_agricultural_land": 0.6875,
                "permanent_crop_share_of_agricultural_land": 0.10,
                "share_of_country_woodland": 0.50,
                "modal_scenario_share_best": 0.85,
                "forest_area_ha": 20_000.0,
                "harvest_total_m3": 1_000.0,
                "selected_food_crop_area_kha": 60.0,
                "selected_food_production_kt": 250.0,
                "food_production_intensity_index": 1.4,
            },
        ]
    )
    scenario_results = pd.DataFrame(
        [
            {
                "country": "Exampleland",
                "country_code": "EX",
                "scenario": "conservation_priority",
                "scenario_label": "Conservation Priority",
                "scenario_description": "Cut harvest.",
                "net_climate_benefit_tco2e": 3000.0,
                "carbon_value_eur": 300_000.0,
                "delta_biodiversity_pressure_proxy": -0.2,
                "changed_harvest_m3": 500.0,
                "harvest_total_m3": 850.0,
            },
            {
                "country": "Exampleland",
                "country_code": "EX",
                "scenario": "material_cascade",
                "scenario_label": "Material Cascade",
                "scenario_description": "Shift to materials.",
                "net_climate_benefit_tco2e": 2400.0,
                "carbon_value_eur": 240_000.0,
                "delta_biodiversity_pressure_proxy": 0.0,
                "changed_harvest_m3": 400.0,
                "harvest_total_m3": 1_000.0,
            },
            {
                "country": "Exampleland",
                "country_code": "EX",
                "scenario": "bioenergy_push",
                "scenario_label": "Bioenergy Push",
                "scenario_description": "Increase harvest.",
                "net_climate_benefit_tco2e": -500.0,
                "carbon_value_eur": -50_000.0,
                "delta_biodiversity_pressure_proxy": 0.2,
                "changed_harvest_m3": 600.0,
                "harvest_total_m3": 1_150.0,
            },
        ]
    )

    policy_options = build_regional_policy_options(nuts2_screening, scenario_results)
    unconstrained = select_regional_policy_priorities(policy_options)
    optimized = optimize_regional_policy_portfolio(policy_options, unconstrained)

    portfolio = optimized["selected_portfolio"].set_index("nuts2_id")
    constraints = optimized["constraint_summary"].set_index("constraint")

    assert portfolio.loc["EX01", "optimized_policy_label"] == "Material Cascade"
    assert portfolio.loc["EX02", "optimized_policy_label"] == FOOD_LAND_POLICY_LABEL
    assert constraints.loc["Biomass supply floor", "achieved_share_of_reference"] >= 0.97
    assert constraints.loc["Food-capacity safeguard floor", "achieved_share_of_reference"] >= 0.22
    assert int(constraints.loc["Biomass supply floor", "switch_count"]) >= 1


def test_regional_policy_options_use_empirical_regional_forest_data_without_double_scaling() -> None:
    nuts2_screening = pd.DataFrame(
        [
            {
                "nuts2_id": "SE99",
                "nuts2_name": "Empirical Forest",
                "country": "Sweden",
                "country_code": "SE",
                "total_area_km2": 120.0,
                "woodland_area_km2": 60.0,
                "cropland_area_km2": 10.0,
                "grassland_area_km2": 8.0,
                "agricultural_land_area_km2": 18.0,
                "feed_land_area_km2": 8.0,
                "woodland_share_of_land": 0.50,
                "cropland_share_of_land": 0.08,
                "grassland_share_of_land": 0.07,
                "agricultural_land_share_of_land": 0.15,
                "feed_land_share_of_agricultural_land": 0.44,
                "permanent_crop_share_of_agricultural_land": 0.05,
                "share_of_country_woodland": 0.20,
                "modal_scenario_share_best": 0.80,
                "forest_area_ha": 8_000.0,
                "harvest_total_m3": 100.0,
                "selected_food_crop_area_kha": 20.0,
                "selected_food_production_kt": 60.0,
                "food_production_intensity_index": 1.0,
            },
            {
                "nuts2_id": "EX01",
                "nuts2_name": "Scaled Forest",
                "country": "Exampleland",
                "country_code": "EX",
                "total_area_km2": 120.0,
                "woodland_area_km2": 60.0,
                "cropland_area_km2": 10.0,
                "grassland_area_km2": 8.0,
                "agricultural_land_area_km2": 18.0,
                "feed_land_area_km2": 8.0,
                "woodland_share_of_land": 0.50,
                "cropland_share_of_land": 0.08,
                "grassland_share_of_land": 0.07,
                "agricultural_land_share_of_land": 0.15,
                "feed_land_share_of_agricultural_land": 0.44,
                "permanent_crop_share_of_agricultural_land": 0.05,
                "share_of_country_woodland": 0.20,
                "modal_scenario_share_best": 0.80,
                "forest_area_ha": 40_000.0,
                "harvest_total_m3": 1_000.0,
                "selected_food_crop_area_kha": 20.0,
                "selected_food_production_kt": 60.0,
                "food_production_intensity_index": 1.0,
            },
        ]
    )
    country_scenarios = pd.DataFrame(
        [
            {
                "country": "Exampleland",
                "country_code": "EX",
                "scenario": "conservation_priority",
                "scenario_label": "Conservation Priority",
                "scenario_description": "Cut harvest.",
                "net_climate_benefit_tco2e": 120.0,
                "carbon_value_eur": 12_000.0,
                "delta_biodiversity_pressure_proxy": -0.1,
                "changed_harvest_m3": 100.0,
                "harvest_total_m3": 900.0,
            },
            {
                "country": "Exampleland",
                "country_code": "EX",
                "scenario": "material_cascade",
                "scenario_label": "Material Cascade",
                "scenario_description": "Shift to materials.",
                "net_climate_benefit_tco2e": 140.0,
                "carbon_value_eur": 14_000.0,
                "delta_biodiversity_pressure_proxy": 0.0,
                "changed_harvest_m3": 80.0,
                "harvest_total_m3": 1_000.0,
            },
            {
                "country": "Exampleland",
                "country_code": "EX",
                "scenario": "bioenergy_push",
                "scenario_label": "Bioenergy Push",
                "scenario_description": "Increase harvest.",
                "net_climate_benefit_tco2e": -30.0,
                "carbon_value_eur": -3_000.0,
                "delta_biodiversity_pressure_proxy": 0.1,
                "changed_harvest_m3": 120.0,
                "harvest_total_m3": 1_120.0,
            },
        ]
    )
    regional_scenarios = pd.DataFrame(
        [
            {
                "nuts2_id": "SE99",
                "scenario": "conservation_priority",
                "scenario_label": "Conservation Priority",
                "scenario_description": "Cut harvest.",
                "net_climate_benefit_tco2e": 16.0,
                "carbon_value_eur": 1_600.0,
                "delta_biodiversity_pressure_proxy": -0.1,
                "changed_harvest_m3": 10.0,
                "harvest_total_m3": 90.0,
            },
            {
                "nuts2_id": "SE99",
                "scenario": "material_cascade",
                "scenario_label": "Material Cascade",
                "scenario_description": "Shift to materials.",
                "net_climate_benefit_tco2e": 22.0,
                "carbon_value_eur": 2_200.0,
                "delta_biodiversity_pressure_proxy": 0.0,
                "changed_harvest_m3": 8.0,
                "harvest_total_m3": 100.0,
            },
            {
                "nuts2_id": "SE99",
                "scenario": "bioenergy_push",
                "scenario_label": "Bioenergy Push",
                "scenario_description": "Increase harvest.",
                "net_climate_benefit_tco2e": -5.0,
                "carbon_value_eur": -500.0,
                "delta_biodiversity_pressure_proxy": 0.1,
                "changed_harvest_m3": 12.0,
                "harvest_total_m3": 112.0,
            },
        ]
    )

    options = build_regional_policy_options(
        nuts2_screening,
        country_scenarios,
        regional_scenario_results=regional_scenarios,
    )
    empirical_material = options.loc[
        (options["nuts2_id"] == "SE99") & (options["scenario"] == "material_cascade")
    ].iloc[0]
    scaled_material = options.loc[
        (options["nuts2_id"] == "EX01") & (options["scenario"] == "material_cascade")
    ].iloc[0]

    assert empirical_material["regional_baseline_harvest_m3"] == 100.0
    assert empirical_material["regional_harvest_after_policy_m3"] == 100.0
    assert empirical_material["regional_harvest_change_m3"] == 0.0
    assert empirical_material["estimated_policy_benefit_tco2e"] == 22.0
    assert scaled_material["regional_baseline_harvest_m3"] == 200.0
    assert scaled_material["regional_harvest_after_policy_m3"] == 200.0


def test_constraint_metrics_are_reproducible_and_match_plot_annotations(tmp_path, caplog) -> None:
    nuts2_screening = pd.DataFrame(
        [
            {
                "nuts2_id": "EX01",
                "nuts2_name": "Forest North",
                "country": "Exampleland",
                "country_code": "EX",
                "total_area_km2": 100.0,
                "woodland_area_km2": 70.0,
                "cropland_area_km2": 12.0,
                "grassland_area_km2": 8.0,
                "agricultural_land_area_km2": 20.0,
                "feed_land_area_km2": 8.0,
                "woodland_share_of_land": 0.70,
                "cropland_share_of_land": 0.12,
                "grassland_share_of_land": 0.08,
                "agricultural_land_share_of_land": 0.20,
                "feed_land_share_of_agricultural_land": 0.40,
                "permanent_crop_share_of_agricultural_land": 0.05,
                "share_of_country_woodland": 0.50,
                "modal_scenario_share_best": 0.85,
                "forest_area_ha": 20_000.0,
                "harvest_total_m3": 1_000.0,
                "selected_food_crop_area_kha": 60.0,
                "selected_food_production_kt": 250.0,
                "food_production_intensity_index": 0.9,
            },
            {
                "nuts2_id": "EX02",
                "nuts2_name": "Agri South",
                "country": "Exampleland",
                "country_code": "EX",
                "total_area_km2": 100.0,
                "woodland_area_km2": 30.0,
                "cropland_area_km2": 55.0,
                "grassland_area_km2": 25.0,
                "agricultural_land_area_km2": 80.0,
                "feed_land_area_km2": 55.0,
                "woodland_share_of_land": 0.30,
                "cropland_share_of_land": 0.55,
                "grassland_share_of_land": 0.25,
                "agricultural_land_share_of_land": 0.80,
                "feed_land_share_of_agricultural_land": 0.6875,
                "permanent_crop_share_of_agricultural_land": 0.10,
                "share_of_country_woodland": 0.50,
                "modal_scenario_share_best": 0.85,
                "forest_area_ha": 20_000.0,
                "harvest_total_m3": 1_000.0,
                "selected_food_crop_area_kha": 60.0,
                "selected_food_production_kt": 250.0,
                "food_production_intensity_index": 1.4,
            },
        ]
    )
    scenario_results = pd.DataFrame(
        [
            {
                "country": "Exampleland",
                "country_code": "EX",
                "scenario": "conservation_priority",
                "scenario_label": "Conservation Priority",
                "scenario_description": "Cut harvest.",
                "net_climate_benefit_tco2e": 3000.0,
                "carbon_value_eur": 300_000.0,
                "delta_biodiversity_pressure_proxy": -0.2,
                "changed_harvest_m3": 500.0,
                "harvest_total_m3": 850.0,
            },
            {
                "country": "Exampleland",
                "country_code": "EX",
                "scenario": "material_cascade",
                "scenario_label": "Material Cascade",
                "scenario_description": "Shift to materials.",
                "net_climate_benefit_tco2e": 2400.0,
                "carbon_value_eur": 240_000.0,
                "delta_biodiversity_pressure_proxy": 0.0,
                "changed_harvest_m3": 400.0,
                "harvest_total_m3": 1_000.0,
            },
            {
                "country": "Exampleland",
                "country_code": "EX",
                "scenario": "bioenergy_push",
                "scenario_label": "Bioenergy Push",
                "scenario_description": "Increase harvest.",
                "net_climate_benefit_tco2e": -500.0,
                "carbon_value_eur": -50_000.0,
                "delta_biodiversity_pressure_proxy": 0.2,
                "changed_harvest_m3": 600.0,
                "harvest_total_m3": 1_150.0,
            },
        ]
    )
    policy_options = build_regional_policy_options(nuts2_screening, scenario_results)
    unconstrained = select_regional_policy_priorities(policy_options)

    caplog.set_level("INFO")
    optimized_first = optimize_regional_policy_portfolio(policy_options, unconstrained)
    optimized_second = optimize_regional_policy_portfolio(policy_options, unconstrained)

    pd.testing.assert_frame_equal(
        optimized_first["constraint_summary"].reset_index(drop=True),
        optimized_second["constraint_summary"].reset_index(drop=True),
    )
    validate_constraint_metrics(optimized_first["constraint_summary"])

    constraint_path = tmp_path / "constraint_summary.csv"
    optimized_first["constraint_summary"].to_csv(constraint_path, index=False)
    reloaded = pd.read_csv(constraint_path)
    pd.testing.assert_frame_equal(
        optimized_first["constraint_summary"].reset_index(drop=True),
        reloaded.reset_index(drop=True),
        check_dtype=False,
    )

    plot_metrics = _optimized_constraint_plot_metrics(optimized_first["constraint_summary"])
    for row in plot_metrics.itertuples(index=False):
        assert row.achieved_ratio_label == f"{row.achieved_share_of_requirement:.2f}× ({row.achieved_share_of_requirement:.0%})"
        assert row.delta_ratio_label == f"{row.delta_share_of_requirement:+.2f}"

    logged_text = "\n".join(record.message for record in caplog.records)
    for line in constraint_debug_lines(optimized_first["constraint_summary"]):
        assert line in logged_text
