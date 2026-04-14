from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from .config import (
    DEFAULT_MODEL_PARAMETERS,
    SENSITIVITY_PARAMETER_RANGES,
    SENSITIVITY_RANDOM_SEED,
    SENSITIVITY_SAMPLE_SIZE,
)
from .model import best_scenario_by_country, build_baseline_metrics, evaluate_scenarios, summarize_scenarios


def sample_model_parameters(
    sample_size: int = SENSITIVITY_SAMPLE_SIZE,
    seed: int = SENSITIVITY_RANDOM_SEED,
) -> tuple[list, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    parameter_rows = []
    parameter_sets = []

    for draw_id in range(sample_size):
        overrides = {
            name: float(rng.uniform(low, high))
            for name, (low, high) in SENSITIVITY_PARAMETER_RANGES.items()
        }
        parameter_sets.append(replace(DEFAULT_MODEL_PARAMETERS, **overrides))
        parameter_rows.append({"draw_id": draw_id, **overrides})

    return parameter_sets, pd.DataFrame(parameter_rows)


def _quantile(series: pd.Series, q: float) -> float:
    return float(series.quantile(q))


def run_sensitivity_analysis(
    baseline_inputs: pd.DataFrame,
    sample_size: int = SENSITIVITY_SAMPLE_SIZE,
    seed: int = SENSITIVITY_RANDOM_SEED,
) -> dict[str, pd.DataFrame]:
    parameter_sets, parameter_draws = sample_model_parameters(sample_size=sample_size, seed=seed)

    scenario_result_frames = []
    eu_summary_frames = []
    best_scenario_frames = []

    for draw_id, parameter_set in zip(parameter_draws["draw_id"], parameter_sets, strict=True):
        baseline_metrics = build_baseline_metrics(baseline_inputs, parameters=parameter_set)
        scenario_results = evaluate_scenarios(baseline_metrics, parameters=parameter_set)
        eu_summary = summarize_scenarios(scenario_results)
        best_scenarios = best_scenario_by_country(scenario_results)

        scenario_result_frames.append(
            scenario_results[
                [
                    "country",
                    "country_code",
                    "iso3_code",
                    "scenario",
                    "scenario_label",
                    "net_climate_benefit_tco2e",
                    "net_climate_benefit_tco2e_per_ha",
                    "carbon_value_eur_per_ha",
                    "delta_biodiversity_pressure_proxy",
                ]
            ].assign(draw_id=draw_id)
        )
        eu_summary_frames.append(eu_summary.assign(draw_id=draw_id))
        best_scenario_frames.append(
            best_scenarios[
                [
                    "country",
                    "country_code",
                    "iso3_code",
                    "scenario",
                    "scenario_label",
                    "net_climate_benefit_tco2e_per_ha",
                    "carbon_value_eur_per_ha",
                ]
            ].assign(draw_id=draw_id)
        )

    scenario_results = pd.concat(scenario_result_frames, ignore_index=True)
    eu_summaries = pd.concat(eu_summary_frames, ignore_index=True)
    best_scenarios = pd.concat(best_scenario_frames, ignore_index=True)

    eligible_eu = eu_summaries.loc[eu_summaries["scenario"] != "baseline"].copy()
    eu_best = eligible_eu.loc[eligible_eu.groupby("draw_id")["net_climate_benefit_tco2e"].idxmax()].copy()
    eu_best_frequency = (
        eu_best.groupby(["scenario", "scenario_label"], as_index=False)
        .size()
        .rename(columns={"size": "draws_best"})
    )
    eu_best_frequency["share_best"] = eu_best_frequency["draws_best"] / sample_size

    eu_uncertainty_summary = (
        eligible_eu.groupby(["scenario", "scenario_label"], as_index=False)
        .agg(
            mean_net_climate_benefit_tco2e=("net_climate_benefit_tco2e", "mean"),
            median_net_climate_benefit_tco2e=("net_climate_benefit_tco2e", "median"),
            p10_net_climate_benefit_tco2e=("net_climate_benefit_tco2e", lambda s: _quantile(s, 0.10)),
            p90_net_climate_benefit_tco2e=("net_climate_benefit_tco2e", lambda s: _quantile(s, 0.90)),
            min_net_climate_benefit_tco2e=("net_climate_benefit_tco2e", "min"),
            max_net_climate_benefit_tco2e=("net_climate_benefit_tco2e", "max"),
            share_positive=("net_climate_benefit_tco2e", lambda s: float((s > 0).mean())),
        )
        .merge(eu_best_frequency, on=["scenario", "scenario_label"], how="left")
    )

    country_robustness = (
        best_scenarios.groupby(["country", "country_code", "iso3_code", "scenario", "scenario_label"], as_index=False)
        .size()
        .rename(columns={"size": "draws_best"})
    )
    country_robustness["share_best"] = country_robustness["draws_best"] / sample_size

    sorted_country_robustness = country_robustness.sort_values(
        ["country", "share_best", "scenario_label"],
        ascending=[True, False, True],
    ).reset_index(drop=True)

    modal = sorted_country_robustness.groupby("country", as_index=False).first()
    runner_up = sorted_country_robustness.groupby("country", as_index=False).nth(1).reset_index(drop=True)
    runner_up = runner_up[["country", "scenario_label", "share_best"]].rename(
        columns={
            "scenario_label": "runner_up_scenario_label",
            "share_best": "runner_up_share_best",
        }
    )
    country_modal = modal.merge(runner_up, on="country", how="left")
    country_modal["runner_up_share_best"] = country_modal["runner_up_share_best"].fillna(0.0)
    country_modal["robustness_margin"] = country_modal["share_best"] - country_modal["runner_up_share_best"]

    return {
        "parameter_draws": parameter_draws,
        "scenario_results": scenario_results,
        "eu_summaries": eu_summaries,
        "eu_uncertainty_summary": eu_uncertainty_summary,
        "eu_best_frequency": eu_best_frequency,
        "country_robustness": country_robustness,
        "country_modal_scenario": country_modal,
        "best_scenarios_by_draw": best_scenarios,
    }
