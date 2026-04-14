from __future__ import annotations

import numpy as np
import pandas as pd

from .config import DEFAULT_MODEL_PARAMETERS, ModelParameters, SCENARIOS


def _safe_divide(numerator: float | pd.Series, denominator: float | pd.Series) -> float | pd.Series:
    if isinstance(denominator, pd.Series):
        valid_denominator = denominator.where(denominator > 0.0)
        return numerator / valid_denominator
    if denominator <= 0.0:
        return np.nan
    return numerator / denominator


def build_baseline_metrics(
    inputs: pd.DataFrame,
    parameters: ModelParameters = DEFAULT_MODEL_PARAMETERS,
    reference_metrics: pd.DataFrame | None = None,
) -> pd.DataFrame:
    df = inputs.copy()
    df["forest_area_ha"] = df["forest_area_kha"] * 1_000.0
    df["forest_carbon_stock_mtco2e"] = df["forest_carbon_stock_mt_c"] * (44.0 / 12.0)
    df["carbon_stock_density_tco2e_per_ha"] = _safe_divide(df["forest_carbon_stock_mtco2e"] * 1_000_000.0, df["forest_area_ha"])
    df["harvest_total_m3"] = df["industrial_roundwood_m3"] + df["wood_fuel_m3"]
    df["harvest_intensity_m3_per_ha"] = _safe_divide(df["harvest_total_m3"], df["forest_area_ha"])
    df["wood_fuel_share"] = _safe_divide(df["wood_fuel_m3"], df["harvest_total_m3"])
    df["naturally_regenerating_share"] = _safe_divide(df["naturally_regenerating_forest_kha"], df["forest_area_kha"])
    df["planted_share"] = _safe_divide(df["planted_forest_kha"], df["forest_area_kha"])
    df["primary_forest_share"] = _safe_divide(df["primary_forest_kha"], df["forest_area_kha"])
    df["material_recovery_ratio"] = _safe_divide(df["sawnwood_m3"], df["industrial_roundwood_m3"])
    df["biodiversity_pressure_proxy"] = df["harvest_intensity_m3_per_ha"] * df["naturally_regenerating_share"]
    df["has_positive_forest_area"] = df["forest_area_ha"] > 0.0
    df["has_positive_baseline_harvest"] = df["harvest_total_m3"] > 0.0
    df["forest_policy_eligible"] = df["has_positive_forest_area"] & df["has_positive_baseline_harvest"]

    if "selected_food_crop_area_kha" in df.columns:
        df["selected_food_crop_area_ha"] = df["selected_food_crop_area_kha"] * 1_000.0
        df["selected_food_crop_share_of_forest_area"] = _safe_divide(df["selected_food_crop_area_ha"], df["forest_area_ha"])
    if "food_production_intensity_index" not in df.columns:
        df["food_production_intensity_index"] = 0.0

    if reference_metrics is None:
        reference_pressure = df["harvest_intensity_m3_per_ha"].median()
        reference_carbon_density = df["carbon_stock_density_tco2e_per_ha"].median()
    else:
        reference_pressure = reference_metrics["harvest_intensity_m3_per_ha"].median()
        reference_carbon_density = reference_metrics["carbon_stock_density_tco2e_per_ha"].median()

    pressure_factor = df["harvest_intensity_m3_per_ha"] / reference_pressure
    carbon_factor = df["carbon_stock_density_tco2e_per_ha"] / reference_carbon_density
    df["forest_carbon_opportunity_cost_tco2e_per_m3"] = (
        parameters.base_forest_carbon_opportunity_cost_tco2e_per_m3
        + parameters.pressure_sensitivity * (pressure_factor - 1.0)
        + parameters.carbon_density_sensitivity * (carbon_factor - 1.0)
    ).clip(
        lower=parameters.min_forest_carbon_opportunity_cost_tco2e_per_m3,
        upper=parameters.max_forest_carbon_opportunity_cost_tco2e_per_m3,
    )

    return df


def _scenario_volumes(
    row: pd.Series,
    scenario_name: str,
    parameters: ModelParameters = DEFAULT_MODEL_PARAMETERS,
) -> dict[str, float]:
    industrial = float(row["industrial_roundwood_m3"])
    wood_fuel = float(row["wood_fuel_m3"])
    total_harvest = industrial + wood_fuel

    if scenario_name == "baseline":
        return {
            "industrial_roundwood_m3": industrial,
            "wood_fuel_m3": wood_fuel,
            "harvest_total_m3": total_harvest,
            "shifted_volume_m3": 0.0,
            "changed_harvest_m3": 0.0,
        }

    if scenario_name == "conservation_priority":
        reduction = parameters.harvest_reduction_share * total_harvest
        wood_fuel_cut = min(wood_fuel, reduction)
        industrial_cut = max(0.0, reduction - wood_fuel_cut)
        return {
            "industrial_roundwood_m3": industrial - industrial_cut,
            "wood_fuel_m3": wood_fuel - wood_fuel_cut,
            "harvest_total_m3": total_harvest - reduction,
            "shifted_volume_m3": 0.0,
            "changed_harvest_m3": reduction,
        }

    if scenario_name == "material_cascade":
        shift = parameters.wood_fuel_to_material_shift_share * wood_fuel
        return {
            "industrial_roundwood_m3": industrial + shift,
            "wood_fuel_m3": wood_fuel - shift,
            "harvest_total_m3": total_harvest,
            "shifted_volume_m3": shift,
            "changed_harvest_m3": shift,
        }

    if scenario_name == "bioenergy_push":
        addition = parameters.harvest_increase_share * total_harvest
        return {
            "industrial_roundwood_m3": industrial,
            "wood_fuel_m3": wood_fuel + addition,
            "harvest_total_m3": total_harvest + addition,
            "shifted_volume_m3": 0.0,
            "changed_harvest_m3": addition,
        }

    raise ValueError(f"Unknown scenario: {scenario_name}")


def _absolute_climate_score(
    row: pd.Series,
    industrial_roundwood_m3: float,
    wood_fuel_m3: float,
    parameters: ModelParameters = DEFAULT_MODEL_PARAMETERS,
) -> dict[str, float]:
    supply_chain = (
        industrial_roundwood_m3 * parameters.supply_chain_material_tco2e_per_m3
        + wood_fuel_m3 * parameters.supply_chain_bioenergy_tco2e_per_m3
    )
    substitution = (
        industrial_roundwood_m3 * parameters.substitution_material_tco2e_per_m3
        + wood_fuel_m3 * parameters.substitution_bioenergy_tco2e_per_m3
    )
    forest_carbon_cost = (
        (industrial_roundwood_m3 + wood_fuel_m3)
        * row["forest_carbon_opportunity_cost_tco2e_per_m3"]
    )
    return {
        "absolute_supply_chain_tco2e": supply_chain,
        "absolute_substitution_tco2e": substitution,
        "absolute_forest_carbon_cost_tco2e": forest_carbon_cost,
        "absolute_net_climate_score_tco2e": substitution - supply_chain - forest_carbon_cost,
    }


def evaluate_scenarios(
    baseline_df: pd.DataFrame,
    parameters: ModelParameters = DEFAULT_MODEL_PARAMETERS,
) -> pd.DataFrame:
    passthrough_columns = [
        column
        for column in ["nuts2_id", "nuts2_name", "parent_country", "source_layer"]
        if column in baseline_df.columns
    ]
    baseline_scores = []
    for row in baseline_df.itertuples(index=False):
        row_series = pd.Series(row._asdict())
        absolute = _absolute_climate_score(
            row_series,
            industrial_roundwood_m3=row.industrial_roundwood_m3,
            wood_fuel_m3=row.wood_fuel_m3,
            parameters=parameters,
        )
        baseline_scores.append(
            {
                "country": row.country,
                "absolute_supply_chain_tco2e": absolute["absolute_supply_chain_tco2e"],
                "absolute_substitution_tco2e": absolute["absolute_substitution_tco2e"],
                "absolute_forest_carbon_cost_tco2e": absolute["absolute_forest_carbon_cost_tco2e"],
                "absolute_net_climate_score_tco2e": absolute["absolute_net_climate_score_tco2e"],
            }
        )
    baseline_scores_df = pd.DataFrame(baseline_scores)
    df = baseline_df.merge(baseline_scores_df, on="country", how="left")

    records: list[dict[str, float | str]] = []
    scenario_lookup = {scenario.name: scenario for scenario in SCENARIOS}

    for _, row in df.iterrows():
        base_supply = row["absolute_supply_chain_tco2e"]
        base_substitution = row["absolute_substitution_tco2e"]
        base_forest_cost = row["absolute_forest_carbon_cost_tco2e"]

        for scenario_name, scenario in scenario_lookup.items():
            volumes = _scenario_volumes(row, scenario_name, parameters=parameters)
            absolute = _absolute_climate_score(
                row,
                industrial_roundwood_m3=volumes["industrial_roundwood_m3"],
                wood_fuel_m3=volumes["wood_fuel_m3"],
                parameters=parameters,
            )
            scenario_harvest_intensity = _safe_divide(volumes["harvest_total_m3"], row["forest_area_ha"])
            scenario_pressure = scenario_harvest_intensity * row["naturally_regenerating_share"]

            supply_chain_savings = base_supply - absolute["absolute_supply_chain_tco2e"]
            substitution_gain = absolute["absolute_substitution_tco2e"] - base_substitution
            forest_carbon_retention = base_forest_cost - absolute["absolute_forest_carbon_cost_tco2e"]
            net_climate_benefit = supply_chain_savings + substitution_gain + forest_carbon_retention

            denominator = volumes["changed_harvest_m3"]
            marginal_benefit = _safe_divide(net_climate_benefit, denominator)
            benefit_per_forest_ha = _safe_divide(net_climate_benefit, row["forest_area_ha"])
            value_eur = net_climate_benefit * parameters.carbon_price_eur_per_tco2
            value_per_forest_ha = _safe_divide(value_eur, row["forest_area_ha"])

            records.append(
                {
                    **{column: row[column] for column in passthrough_columns},
                    "country": row["country"],
                    "country_code": row["country_code"],
                    "iso3_code": row["iso3_code"],
                    "scenario": scenario_name,
                    "scenario_label": scenario.label,
                    "scenario_description": scenario.description,
                    "forest_area_ha": row["forest_area_ha"],
                    "harvest_total_m3": volumes["harvest_total_m3"],
                    "industrial_roundwood_m3": volumes["industrial_roundwood_m3"],
                    "wood_fuel_m3": volumes["wood_fuel_m3"],
                    "changed_harvest_m3": volumes["changed_harvest_m3"],
                    "shifted_volume_m3": volumes["shifted_volume_m3"],
                    "harvest_intensity_m3_per_ha": scenario_harvest_intensity,
                    "biodiversity_pressure_proxy": scenario_pressure,
                    "delta_biodiversity_pressure_proxy": scenario_pressure - row["biodiversity_pressure_proxy"],
                    "supply_chain_savings_tco2e": supply_chain_savings,
                    "substitution_gain_tco2e": substitution_gain,
                    "forest_carbon_retention_tco2e": forest_carbon_retention,
                    "net_climate_benefit_tco2e": net_climate_benefit,
                    "net_climate_benefit_tco2e_per_ha": benefit_per_forest_ha,
                    "benefit_tco2e_per_forest_ha": benefit_per_forest_ha,
                    "marginal_climate_benefit_tco2e_per_changed_m3": marginal_benefit,
                    "carbon_value_eur": value_eur,
                    "carbon_value_eur_per_ha": value_per_forest_ha,
                    "value_eur_per_forest_ha": value_per_forest_ha,
                    "value_metric_basis": "forest_ha",
                    "is_forest_only": True,
                    "includes_food_policy": False,
                    "available_policy_options": "conservation_priority|material_cascade|bioenergy_push",
                    "excluded_policy_categories": "food_land_safeguard",
                    "forest_policy_eligible": bool(row.get("forest_policy_eligible", False)),
                    "forest_carbon_opportunity_cost_tco2e_per_m3": row["forest_carbon_opportunity_cost_tco2e_per_m3"],
                    "carbon_stock_density_tco2e_per_ha": row["carbon_stock_density_tco2e_per_ha"],
                    "wood_fuel_share_baseline": row["wood_fuel_share"],
                    "material_recovery_ratio": row["material_recovery_ratio"],
                    "naturally_regenerating_share": row["naturally_regenerating_share"],
                    "planted_share": row["planted_share"],
                }
            )

    return pd.DataFrame.from_records(records)


def summarize_scenarios(scenario_results: pd.DataFrame) -> pd.DataFrame:
    return (
        scenario_results
        .groupby(["scenario", "scenario_label"], as_index=False)[
            [
                "supply_chain_savings_tco2e",
                "substitution_gain_tco2e",
                "forest_carbon_retention_tco2e",
                "net_climate_benefit_tco2e",
                "carbon_value_eur",
            ]
        ]
        .sum()
    )


def best_scenario_by_country(scenario_results: pd.DataFrame) -> pd.DataFrame:
    eligible = scenario_results.loc[
        (scenario_results["scenario"] != "baseline") & (scenario_results["forest_policy_eligible"].fillna(False))
    ].copy()
    if eligible.empty:
        return eligible
    group_column = "nuts2_id" if "nuts2_id" in eligible.columns else "country"
    idx = eligible.groupby(group_column)["value_eur_per_forest_ha"].idxmax()
    return eligible.loc[idx].sort_values(group_column).reset_index(drop=True)


def ranking_table(scenario_results: pd.DataFrame) -> pd.DataFrame:
    eligible = scenario_results.loc[
        (scenario_results["scenario"] != "baseline") & (scenario_results["forest_policy_eligible"].fillna(False))
    ].copy()
    ranking = eligible.sort_values("value_eur_per_forest_ha", ascending=False).reset_index(drop=True)
    ranking["rank"] = np.arange(1, len(ranking) + 1)
    return ranking[
        [
            "rank",
            "country",
            "scenario_label",
            "value_eur_per_forest_ha",
            "benefit_tco2e_per_forest_ha",
            "marginal_climate_benefit_tco2e_per_changed_m3",
            "delta_biodiversity_pressure_proxy",
        ]
    ]
