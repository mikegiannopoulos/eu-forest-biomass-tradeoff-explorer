from __future__ import annotations

import pandas as pd

from .config import AllocationParameters, DEFAULT_ALLOCATION_PARAMETERS


FOOD_LAND_POLICY_NAME = "food_land_safeguard"
FOOD_LAND_POLICY_LABEL = "Food-Land Safeguard"
FOREST_POLICY_SET = "conservation_priority|material_cascade|bioenergy_push"
INTEGRATED_POLICY_SET = f"{FOREST_POLICY_SET}|{FOOD_LAND_POLICY_NAME}"
FOOD_LAND_POLICY_DESCRIPTION = (
    "Treat agricultural land as a constrained food and feed resource, and value retaining a small "
    "share of cropland and grassland against diversion into additional biomass supply."
)


def _share(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    valid_denominator = denominator.where(denominator > 0.0)
    return (numerator / valid_denominator).fillna(0.0)


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    valid_denominator = denominator.where(denominator > 0.0)
    return numerator / valid_denominator


def build_regional_policy_options(
    nuts2_screening_gdf: pd.DataFrame,
    scenario_results: pd.DataFrame,
    regional_scenario_results: pd.DataFrame | None = None,
    parameters: AllocationParameters = DEFAULT_ALLOCATION_PARAMETERS,
) -> pd.DataFrame:
    screening = nuts2_screening_gdf.copy()
    for column in [
        "forest_area_ha",
        "harvest_total_m3",
        "selected_food_crop_area_kha",
        "selected_food_production_kt",
        "food_production_intensity_index",
    ]:
        if column not in screening.columns:
            screening[column] = 0.0

    regional_base = (
        screening[
            [
                "nuts2_id",
                "nuts2_name",
                "country",
                "country_code",
                "total_area_km2",
                "woodland_area_km2",
                "cropland_area_km2",
                "grassland_area_km2",
                "agricultural_land_area_km2",
                "feed_land_area_km2",
                "woodland_share_of_land",
                "cropland_share_of_land",
                "grassland_share_of_land",
                "agricultural_land_share_of_land",
                "feed_land_share_of_agricultural_land",
                "permanent_crop_share_of_agricultural_land",
                "share_of_country_woodland",
                "modal_scenario_share_best",
                "forest_area_ha",
                "harvest_total_m3",
                "selected_food_crop_area_kha",
                "selected_food_production_kt",
                "food_production_intensity_index",
            ]
        ]
        .drop_duplicates(subset=["nuts2_id"])
        .copy()
    )
    regional_base["total_land_area_ha"] = regional_base["total_area_km2"] * 100.0
    regional_base["agricultural_land_area_ha"] = regional_base["agricultural_land_area_km2"] * 100.0
    regional_base = regional_base.rename(columns={"harvest_total_m3": "baseline_harvest_input_m3"})
    regional_base["cropland_share_of_agricultural_land"] = _share(
        regional_base["cropland_area_km2"],
        regional_base["agricultural_land_area_km2"],
    )
    empirical_nuts2_ids: set[str] = set()
    if regional_scenario_results is not None and "nuts2_id" in regional_scenario_results.columns:
        empirical_nuts2_ids = set(regional_scenario_results["nuts2_id"].dropna().unique().tolist())
    regional_base["uses_regional_forest_data"] = regional_base["nuts2_id"].isin(empirical_nuts2_ids)
    regional_base["regional_baseline_harvest_m3"] = regional_base["baseline_harvest_input_m3"].where(
        regional_base["uses_regional_forest_data"],
        regional_base["baseline_harvest_input_m3"] * regional_base["share_of_country_woodland"],
    )
    regional_base["regional_estimated_forest_area_ha"] = regional_base["forest_area_ha"].where(
        regional_base["uses_regional_forest_data"],
        regional_base["forest_area_ha"] * regional_base["share_of_country_woodland"],
    )
    regional_base["food_production_intensity_index"] = regional_base["food_production_intensity_index"].fillna(0.0)
    regional_base["selected_food_crop_area_kha"] = regional_base["selected_food_crop_area_kha"].fillna(0.0)
    regional_base["selected_food_production_kt"] = regional_base["selected_food_production_kt"].fillna(0.0)

    country_forest_options = scenario_results.loc[scenario_results["scenario"] != "baseline"].copy()
    country_forest_options = country_forest_options[
        [
            "country",
            "country_code",
            "scenario",
            "scenario_label",
            "scenario_description",
            "net_climate_benefit_tco2e",
            "carbon_value_eur",
            "delta_biodiversity_pressure_proxy",
            "changed_harvest_m3",
            "harvest_total_m3",
        ]
    ].rename(columns={"harvest_total_m3": "scenario_harvest_total_m3"})
    country_forest_options = regional_base.loc[~regional_base["uses_regional_forest_data"]].merge(
        country_forest_options,
        on=["country", "country_code"],
        how="left",
    )
    country_forest_options["estimated_policy_benefit_tco2e"] = (
        country_forest_options["net_climate_benefit_tco2e"] * country_forest_options["share_of_country_woodland"]
    )
    country_forest_options["policy_value_eur"] = (
        country_forest_options["carbon_value_eur"] * country_forest_options["share_of_country_woodland"]
    )
    country_forest_options["regional_harvest_after_policy_m3"] = (
        country_forest_options["scenario_harvest_total_m3"] * country_forest_options["share_of_country_woodland"]
    )

    regional_forest_options = pd.DataFrame(columns=country_forest_options.columns)
    if regional_scenario_results is not None and empirical_nuts2_ids:
        regional_lookup = regional_scenario_results.loc[regional_scenario_results["scenario"] != "baseline"].copy()
        regional_lookup = regional_lookup[
            [
                "nuts2_id",
                "scenario",
                "scenario_label",
                "scenario_description",
                "net_climate_benefit_tco2e",
                "carbon_value_eur",
                "delta_biodiversity_pressure_proxy",
                "changed_harvest_m3",
                "harvest_total_m3",
            ]
        ].rename(columns={"harvest_total_m3": "scenario_harvest_total_m3"})
        regional_forest_options = regional_base.loc[regional_base["uses_regional_forest_data"]].merge(
            regional_lookup,
            on="nuts2_id",
            how="left",
        )
        regional_forest_options["estimated_policy_benefit_tco2e"] = regional_forest_options["net_climate_benefit_tco2e"]
        regional_forest_options["policy_value_eur"] = regional_forest_options["carbon_value_eur"]
        regional_forest_options["regional_harvest_after_policy_m3"] = regional_forest_options["scenario_harvest_total_m3"]

    forest_options = pd.concat([country_forest_options, regional_forest_options], ignore_index=True)
    forest_options["option_type"] = "forest_biomass"
    forest_options["marginal_target_area_ha"] = forest_options["woodland_area_km2"] * 100.0
    forest_options["marginal_cropland_target_area_ha"] = 0.0
    forest_options["food_land_displacement_proxy_tco2e_per_ha"] = 0.0
    forest_options["food_capacity_indexed_ha"] = 0.0
    forest_options["regional_harvest_change_m3"] = (
        forest_options["regional_harvest_after_policy_m3"] - forest_options["regional_baseline_harvest_m3"]
    )
    forest_options["forest_policy_eligible"] = (
        (forest_options["regional_estimated_forest_area_ha"] > 0.0)
        & (forest_options["regional_baseline_harvest_m3"] > 0.0)
    )
    forest_options["policy_option_eligible"] = forest_options["forest_policy_eligible"]
    forest_options["policy_value_eur_per_ha_land"] = (
        forest_options["policy_value_eur"] / forest_options["total_land_area_ha"]
    )
    forest_options["policy_benefit_tco2e_per_ha_land"] = (
        forest_options["estimated_policy_benefit_tco2e"] / forest_options["total_land_area_ha"]
    )
    forest_options["value_eur_per_land_ha"] = forest_options["policy_value_eur_per_ha_land"]
    forest_options["benefit_tco2e_per_land_ha"] = forest_options["policy_benefit_tco2e_per_ha_land"]
    forest_options["value_eur_per_forest_ha"] = _safe_divide(
        forest_options["policy_value_eur"],
        forest_options["regional_estimated_forest_area_ha"],
    )
    forest_options["benefit_tco2e_per_forest_ha"] = _safe_divide(
        forest_options["estimated_policy_benefit_tco2e"],
        forest_options["regional_estimated_forest_area_ha"],
    )
    forest_options["is_forest_only"] = False
    forest_options["includes_food_policy"] = True
    forest_options["available_policy_options"] = INTEGRATED_POLICY_SET
    forest_options["excluded_policy_categories"] = ""

    food_options = regional_base.copy()
    food_options["scenario"] = FOOD_LAND_POLICY_NAME
    food_options["scenario_label"] = FOOD_LAND_POLICY_LABEL
    food_options["scenario_description"] = FOOD_LAND_POLICY_DESCRIPTION
    food_options["option_type"] = "food_land"
    food_options["changed_harvest_m3"] = 0.0
    food_options["delta_biodiversity_pressure_proxy"] = 0.0
    food_options["regional_harvest_after_policy_m3"] = food_options["regional_baseline_harvest_m3"]
    food_options["regional_harvest_change_m3"] = 0.0
    food_options["marginal_target_area_ha"] = (
        food_options["agricultural_land_area_km2"]
        * 100.0
        * parameters.marginal_agricultural_land_reallocation_share
    )
    food_options["marginal_cropland_target_area_ha"] = (
        food_options["marginal_target_area_ha"] * food_options["cropland_share_of_agricultural_land"]
    )
    food_options["food_land_displacement_proxy_tco2e_per_ha"] = (
        parameters.base_food_land_displacement_tco2e_per_ha
        + parameters.feed_land_displacement_sensitivity * food_options["feed_land_share_of_agricultural_land"]
        + parameters.permanent_crop_displacement_sensitivity * food_options["permanent_crop_share_of_agricultural_land"]
        + parameters.food_production_intensity_sensitivity * (food_options["food_production_intensity_index"] - 1.0)
    ).clip(
        lower=parameters.min_food_land_displacement_tco2e_per_ha,
        upper=parameters.max_food_land_displacement_tco2e_per_ha,
    )
    food_options["food_capacity_indexed_ha"] = (
        food_options["marginal_cropland_target_area_ha"] * food_options["food_production_intensity_index"]
    )
    food_options["estimated_policy_benefit_tco2e"] = (
        food_options["marginal_target_area_ha"] * food_options["food_land_displacement_proxy_tco2e_per_ha"]
    )
    food_options["policy_value_eur"] = (
        food_options["estimated_policy_benefit_tco2e"] * parameters.carbon_price_eur_per_tco2
    )
    food_options["policy_value_eur_per_ha_land"] = food_options["policy_value_eur"] / food_options["total_land_area_ha"]
    food_options["policy_benefit_tco2e_per_ha_land"] = (
        food_options["estimated_policy_benefit_tco2e"] / food_options["total_land_area_ha"]
    )
    food_options["forest_policy_eligible"] = False
    food_options["policy_option_eligible"] = (
        (food_options["total_land_area_ha"] > 0.0) & (food_options["marginal_target_area_ha"] > 0.0)
    )
    food_options["value_eur_per_land_ha"] = food_options["policy_value_eur_per_ha_land"]
    food_options["benefit_tco2e_per_land_ha"] = food_options["policy_benefit_tco2e_per_ha_land"]
    food_options["value_eur_per_forest_ha"] = pd.NA
    food_options["benefit_tco2e_per_forest_ha"] = pd.NA
    food_options["is_forest_only"] = False
    food_options["includes_food_policy"] = True
    food_options["available_policy_options"] = INTEGRATED_POLICY_SET
    food_options["excluded_policy_categories"] = ""

    option_columns = [
        "nuts2_id",
        "nuts2_name",
        "country",
        "country_code",
        "total_area_km2",
        "total_land_area_ha",
        "woodland_area_km2",
        "cropland_area_km2",
        "grassland_area_km2",
        "agricultural_land_area_km2",
        "feed_land_area_km2",
        "woodland_share_of_land",
        "cropland_share_of_land",
        "grassland_share_of_land",
        "agricultural_land_share_of_land",
        "feed_land_share_of_agricultural_land",
        "permanent_crop_share_of_agricultural_land",
        "cropland_share_of_agricultural_land",
        "share_of_country_woodland",
        "modal_scenario_share_best",
        "regional_estimated_forest_area_ha",
        "regional_baseline_harvest_m3",
        "regional_harvest_after_policy_m3",
        "regional_harvest_change_m3",
        "selected_food_crop_area_kha",
        "selected_food_production_kt",
        "food_production_intensity_index",
        "scenario",
        "scenario_label",
        "scenario_description",
        "option_type",
        "marginal_target_area_ha",
        "marginal_cropland_target_area_ha",
        "changed_harvest_m3",
        "delta_biodiversity_pressure_proxy",
        "food_land_displacement_proxy_tco2e_per_ha",
        "food_capacity_indexed_ha",
        "estimated_policy_benefit_tco2e",
        "policy_benefit_tco2e_per_ha_land",
        "policy_value_eur",
        "policy_value_eur_per_ha_land",
        "benefit_tco2e_per_land_ha",
        "value_eur_per_land_ha",
        "benefit_tco2e_per_forest_ha",
        "value_eur_per_forest_ha",
        "forest_policy_eligible",
        "policy_option_eligible",
        "is_forest_only",
        "includes_food_policy",
        "available_policy_options",
        "excluded_policy_categories",
    ]
    return pd.concat([forest_options[option_columns], food_options[option_columns]], ignore_index=True)


def select_regional_policy_priorities(policy_options: pd.DataFrame) -> pd.DataFrame:
    eligible_options = policy_options.loc[policy_options["policy_option_eligible"].fillna(False)].copy()
    best_idx = eligible_options.groupby("nuts2_id")["value_eur_per_land_ha"].idxmax()
    selected = policy_options.loc[best_idx].copy().rename(
        columns={
            "scenario": "selected_policy",
            "scenario_label": "selected_policy_label",
            "scenario_description": "selected_policy_description",
            "option_type": "selected_policy_type",
            "marginal_target_area_ha": "selected_policy_target_area_ha",
            "marginal_cropland_target_area_ha": "selected_policy_target_cropland_area_ha",
            "estimated_policy_benefit_tco2e": "selected_policy_benefit_tco2e",
            "policy_benefit_tco2e_per_ha_land": "selected_policy_benefit_tco2e_per_ha_land",
            "policy_value_eur": "selected_policy_value_eur",
            "policy_value_eur_per_ha_land": "selected_policy_value_eur_per_ha_land",
            "benefit_tco2e_per_land_ha": "selected_policy_benefit_tco2e_per_land_ha",
            "value_eur_per_land_ha": "selected_policy_value_eur_per_land_ha",
            "benefit_tco2e_per_forest_ha": "selected_policy_benefit_tco2e_per_forest_ha",
            "value_eur_per_forest_ha": "selected_policy_value_eur_per_forest_ha",
            "changed_harvest_m3": "selected_policy_changed_harvest_m3",
            "delta_biodiversity_pressure_proxy": "selected_policy_delta_biodiversity_pressure_proxy",
            "food_land_displacement_proxy_tco2e_per_ha": "selected_policy_food_land_proxy_tco2e_per_ha",
            "regional_harvest_after_policy_m3": "selected_policy_regional_harvest_after_policy_m3",
            "regional_harvest_change_m3": "selected_policy_regional_harvest_change_m3",
            "food_capacity_indexed_ha": "selected_policy_food_capacity_indexed_ha",
        }
    )

    forest_best_idx = (
        policy_options.loc[
            (policy_options["option_type"] == "forest_biomass")
            & (policy_options["forest_policy_eligible"].fillna(False))
        ]
        .groupby("nuts2_id")["value_eur_per_land_ha"]
        .idxmax()
    )
    forest_best = policy_options.loc[forest_best_idx].copy().rename(
        columns={
            "scenario": "best_forest_policy",
            "scenario_label": "best_forest_policy_label",
            "scenario_description": "best_forest_policy_description",
            "estimated_policy_benefit_tco2e": "best_forest_policy_benefit_tco2e",
            "policy_benefit_tco2e_per_ha_land": "best_forest_policy_benefit_tco2e_per_ha_land",
            "policy_value_eur": "best_forest_policy_value_eur",
            "policy_value_eur_per_ha_land": "best_forest_policy_value_eur_per_ha_land",
            "benefit_tco2e_per_land_ha": "best_forest_policy_benefit_tco2e_per_land_ha",
            "value_eur_per_land_ha": "best_forest_policy_value_eur_per_land_ha",
            "benefit_tco2e_per_forest_ha": "best_forest_policy_benefit_tco2e_per_forest_ha",
            "value_eur_per_forest_ha": "best_forest_policy_value_eur_per_forest_ha",
            "regional_harvest_after_policy_m3": "best_forest_policy_regional_harvest_after_policy_m3",
        }
    )[
        [
            "nuts2_id",
            "best_forest_policy",
            "best_forest_policy_label",
            "best_forest_policy_description",
            "best_forest_policy_benefit_tco2e",
            "best_forest_policy_benefit_tco2e_per_ha_land",
            "best_forest_policy_value_eur",
            "best_forest_policy_value_eur_per_ha_land",
            "best_forest_policy_benefit_tco2e_per_land_ha",
            "best_forest_policy_value_eur_per_land_ha",
            "best_forest_policy_benefit_tco2e_per_forest_ha",
            "best_forest_policy_value_eur_per_forest_ha",
            "best_forest_policy_regional_harvest_after_policy_m3",
        ]
    ]

    food_option = policy_options.loc[policy_options["scenario"] == FOOD_LAND_POLICY_NAME].copy().rename(
        columns={
            "estimated_policy_benefit_tco2e": "food_land_policy_benefit_tco2e",
            "policy_benefit_tco2e_per_ha_land": "food_land_policy_benefit_tco2e_per_ha_land",
            "policy_value_eur": "food_land_policy_value_eur",
            "policy_value_eur_per_ha_land": "food_land_policy_value_eur_per_ha_land",
            "benefit_tco2e_per_land_ha": "food_land_policy_benefit_tco2e_per_land_ha",
            "value_eur_per_land_ha": "food_land_policy_value_eur_per_land_ha",
            "marginal_target_area_ha": "food_land_target_area_ha",
            "marginal_cropland_target_area_ha": "food_land_target_cropland_area_ha",
            "food_land_displacement_proxy_tco2e_per_ha": "food_land_displacement_proxy_tco2e_per_ha",
            "food_capacity_indexed_ha": "food_land_capacity_indexed_ha",
        }
    )[
        [
            "nuts2_id",
            "food_land_policy_benefit_tco2e",
            "food_land_policy_benefit_tco2e_per_ha_land",
            "food_land_policy_value_eur",
            "food_land_policy_value_eur_per_ha_land",
            "food_land_policy_benefit_tco2e_per_land_ha",
            "food_land_policy_value_eur_per_land_ha",
            "food_land_target_area_ha",
            "food_land_target_cropland_area_ha",
            "food_land_displacement_proxy_tco2e_per_ha",
            "food_land_capacity_indexed_ha",
        ]
    ]

    selected = selected.merge(forest_best, on="nuts2_id", how="left")
    selected = selected.merge(food_option, on="nuts2_id", how="left")
    selected["switch_from_best_forest"] = selected["best_forest_policy"].notna() & (
        selected["selected_policy"] != selected["best_forest_policy"]
    )
    selected["food_vs_best_forest_margin_eur_per_ha_land"] = (
        selected["food_land_policy_value_eur_per_ha_land"] - selected["best_forest_policy_value_eur_per_ha_land"]
    )
    selected["food_vs_best_forest_margin_eur_per_land_ha"] = (
        selected["food_land_policy_value_eur_per_land_ha"] - selected["best_forest_policy_value_eur_per_land_ha"]
    )
    selected["food_vs_best_forest_margin_tco2e_per_ha_land"] = (
        selected["food_land_policy_benefit_tco2e_per_ha_land"] - selected["best_forest_policy_benefit_tco2e_per_ha_land"]
    )
    selected["is_forest_only"] = False
    selected["includes_food_policy"] = True
    selected["available_policy_options"] = INTEGRATED_POLICY_SET
    selected["excluded_policy_categories"] = ""
    return selected.sort_values(
        ["selected_policy_value_eur_per_land_ha", "nuts2_name"],
        ascending=[False, True],
    ).reset_index(drop=True)


def summarize_policy_priorities(selected_policies: pd.DataFrame) -> pd.DataFrame:
    summary = (
        selected_policies
        .groupby(["selected_policy", "selected_policy_label"], as_index=False)
        .agg(
            region_count=("nuts2_id", "count"),
            total_area_km2=("total_area_km2", "sum"),
            woodland_area_km2=("woodland_area_km2", "sum"),
            agricultural_land_area_km2=("agricultural_land_area_km2", "sum"),
            selected_policy_benefit_tco2e=("selected_policy_benefit_tco2e", "sum"),
            selected_policy_value_eur=("selected_policy_value_eur", "sum"),
            selected_policy_regional_harvest_after_policy_m3=("selected_policy_regional_harvest_after_policy_m3", "sum"),
            regional_baseline_harvest_m3=("regional_baseline_harvest_m3", "sum"),
            selected_policy_food_capacity_indexed_ha=("selected_policy_food_capacity_indexed_ha", "sum"),
        )
    )
    summary["mean_policy_value_eur_per_region"] = summary["selected_policy_value_eur"] / summary["region_count"]
    summary["harvest_retention_share"] = (
        summary["selected_policy_regional_harvest_after_policy_m3"] / summary["regional_baseline_harvest_m3"]
    ).fillna(1.0)
    return summary.sort_values("selected_policy_value_eur", ascending=False).reset_index(drop=True)


def policy_switch_regions(selected_policies: pd.DataFrame, n: int = 30) -> pd.DataFrame:
    switched = selected_policies.loc[selected_policies["switch_from_best_forest"]].copy()
    switched = switched.sort_values("food_vs_best_forest_margin_eur_per_ha_land", ascending=False).head(n)
    return switched[
        [
            "nuts2_id",
            "nuts2_name",
            "country",
            "selected_policy_label",
            "best_forest_policy_label",
            "food_vs_best_forest_margin_eur_per_ha_land",
            "food_land_policy_value_eur_per_ha_land",
            "best_forest_policy_value_eur_per_ha_land",
            "agricultural_land_share_of_land",
            "woodland_share_of_land",
            "feed_land_share_of_agricultural_land",
            "cropland_share_of_agricultural_land",
            "food_production_intensity_index",
        ]
    ]
