from __future__ import annotations

import logging
from pathlib import Path

import geopandas as gpd

from .allocation import (
    build_regional_policy_options,
    policy_switch_regions,
    select_regional_policy_priorities,
    summarize_policy_priorities,
)
from .config import ANALYSIS_YEAR, DATA_PROCESSED_DIR, FIGURES_DIR, OUTPUTS_DIR
from .data import build_baseline_inputs, download_raw_data, ensure_directories, load_country_geometries
from .model import best_scenario_by_country, build_baseline_metrics, evaluate_scenarios, ranking_table, summarize_scenarios
from .optimization import optimize_regional_policy_portfolio
from .plotting import (
    plot_best_scenario_map,
    plot_country_robustness_heatmap,
    plot_eu_uncertainty_ranges,
    plot_forest_food_tradeoff,
    plot_integrated_policy_priority_map,
    plot_integrated_policy_summary,
    plot_nuts2_context_scatter,
    plot_nuts2_priority_map,
    plot_optimized_policy_map,
    plot_optimized_portfolio_summary,
    plot_robust_best_scenario_map,
    plot_scenario_decomposition,
    plot_sweden_empirical_best_scenario_map,
    plot_sweden_empirical_comparison,
    plot_tradeoff_scatter,
)
from .reporting import write_consistency_audit, write_run_manifest
from .regional import (
    build_nuts2_screening_dataset,
    compare_sweden_empirical_to_screening,
    load_nuts2_geometries,
    top_nuts2_regions,
)
from .sensitivity import run_sensitivity_analysis
from .sweden import build_sweden_empirical_nuts2_case_study
from .config import PROJECT_ROOT

logger = logging.getLogger(__name__)


def _write_outputs(
    baseline_metrics,
    scenario_results,
    summary,
    ranking,
    best_scenarios,
    countries_gdf,
    sensitivity_outputs,
    nuts2_screening_gdf,
    nuts2_top_regions,
    policy_options,
    selected_policies,
    policy_summary,
    switch_regions,
    optimized_outputs,
    all_nuts2_gdf,
    sweden_empirical_case,
    sweden_comparison,
) -> None:
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    baseline_metrics.to_csv(DATA_PROCESSED_DIR / "country_baseline_metrics.csv", index=False)
    scenario_results.to_csv(OUTPUTS_DIR / "scenario_results_by_country.csv", index=False)
    summary.to_csv(OUTPUTS_DIR / "scenario_summary_eu.csv", index=False)
    ranking.to_csv(OUTPUTS_DIR / "country_ranking_table.csv", index=False)
    best_scenarios.to_csv(OUTPUTS_DIR / "best_scenario_by_country.csv", index=False)
    sensitivity_outputs["parameter_draws"].to_csv(OUTPUTS_DIR / "sensitivity_parameter_draws.csv", index=False)
    sensitivity_outputs["scenario_results"].to_csv(OUTPUTS_DIR / "sensitivity_scenario_results.csv", index=False)
    sensitivity_outputs["eu_uncertainty_summary"].to_csv(OUTPUTS_DIR / "sensitivity_eu_uncertainty_summary.csv", index=False)
    sensitivity_outputs["eu_best_frequency"].to_csv(OUTPUTS_DIR / "sensitivity_eu_best_frequency.csv", index=False)
    sensitivity_outputs["country_robustness"].to_csv(OUTPUTS_DIR / "sensitivity_country_robustness.csv", index=False)
    sensitivity_outputs["country_modal_scenario"].to_csv(OUTPUTS_DIR / "sensitivity_country_modal_scenario.csv", index=False)
    nuts2_screening_gdf.drop(columns="geometry").to_csv(DATA_PROCESSED_DIR / "nuts2_screening_metrics.csv", index=False)
    sweden_empirical_case["county_metrics"].to_csv(DATA_PROCESSED_DIR / "sweden_county_empirical_metrics.csv", index=False)
    sweden_empirical_case["nuts2_metrics"].to_csv(DATA_PROCESSED_DIR / "sweden_nuts2_empirical_metrics.csv", index=False)
    sweden_empirical_case["baseline_metrics"].to_csv(
        DATA_PROCESSED_DIR / "sweden_nuts2_empirical_baseline_metrics.csv",
        index=False,
    )
    nuts2_top_regions.to_csv(OUTPUTS_DIR / "nuts2_top_regions_table.csv", index=False)
    policy_options.to_csv(OUTPUTS_DIR / "nuts2_integrated_policy_options.csv", index=False)
    selected_policies.to_csv(OUTPUTS_DIR / "nuts2_integrated_policy_priorities.csv", index=False)
    policy_summary.to_csv(OUTPUTS_DIR / "nuts2_integrated_policy_summary.csv", index=False)
    switch_regions.to_csv(OUTPUTS_DIR / "nuts2_policy_switch_regions.csv", index=False)
    optimized_outputs["selected_portfolio"].to_csv(OUTPUTS_DIR / "nuts2_optimized_policy_portfolio.csv", index=False)
    optimized_outputs["policy_summary"].to_csv(OUTPUTS_DIR / "nuts2_optimized_policy_summary.csv", index=False)
    optimized_outputs["constraint_summary"].to_csv(OUTPUTS_DIR / "nuts2_optimized_constraint_summary.csv", index=False)
    optimized_outputs["switch_regions"].to_csv(OUTPUTS_DIR / "nuts2_optimized_policy_switches.csv", index=False)
    sweden_empirical_case["scenario_results"].to_csv(OUTPUTS_DIR / "sweden_nuts2_empirical_scenario_results.csv", index=False)
    sweden_empirical_case["best_scenarios"].to_csv(OUTPUTS_DIR / "sweden_nuts2_empirical_best_scenarios.csv", index=False)
    sweden_comparison.to_csv(OUTPUTS_DIR / "sweden_nuts2_screening_comparison.csv", index=False)
    write_run_manifest(PROJECT_ROOT, OUTPUTS_DIR / "run_manifest.json")
    write_consistency_audit(
        OUTPUTS_DIR / "consistency_audit.md",
        sweden_best_scenarios=sweden_empirical_case["best_scenarios"],
        selected_policies=selected_policies,
        optimized_portfolio=optimized_outputs["selected_portfolio"],
        screening_gdf=nuts2_screening_gdf.drop(columns="geometry"),
        all_nuts2_gdf=all_nuts2_gdf.drop(columns="geometry"),
        baseline_metrics=baseline_metrics,
    )

    map_gdf = countries_gdf.merge(best_scenarios, on=["country", "country_code", "iso3_code"], how="left")
    map_gdf.to_file(DATA_PROCESSED_DIR / "best_scenario_map_data.geojson", driver="GeoJSON")
    robustness_map_gdf = countries_gdf.merge(
        sensitivity_outputs["country_modal_scenario"],
        on=["country", "country_code", "iso3_code"],
        how="left",
    )
    robustness_map_gdf.to_file(DATA_PROCESSED_DIR / "robust_best_scenario_map_data.geojson", driver="GeoJSON")
    nuts2_screening_map_gdf = gpd.GeoDataFrame(
        all_nuts2_gdf.merge(
            nuts2_screening_gdf.drop(columns="geometry"),
            on=["nuts2_id", "country_code", "nuts2_name"],
            how="left",
        ),
        geometry="geometry",
        crs=all_nuts2_gdf.crs,
    )
    nuts2_screening_map_gdf.to_file(DATA_PROCESSED_DIR / "nuts2_screening_map_data.geojson", driver="GeoJSON")
    sweden_empirical_map_gdf = gpd.GeoDataFrame(
        all_nuts2_gdf.loc[all_nuts2_gdf["country_code"] == "SE"].merge(
            sweden_empirical_case["best_scenarios"],
            on="nuts2_id",
            how="left",
        ),
        geometry="geometry",
        crs=all_nuts2_gdf.crs,
    )
    sweden_empirical_map_gdf.to_file(
        DATA_PROCESSED_DIR / "sweden_nuts2_empirical_best_scenario_map_data.geojson",
        driver="GeoJSON",
    )
    integrated_policy_map_gdf = gpd.GeoDataFrame(
        all_nuts2_gdf.merge(
            selected_policies,
            on="nuts2_id",
            how="left",
        ),
        geometry="geometry",
        crs=all_nuts2_gdf.crs,
    )
    integrated_policy_map_gdf.to_file(DATA_PROCESSED_DIR / "nuts2_integrated_policy_map_data.geojson", driver="GeoJSON")
    optimized_policy_map_gdf = gpd.GeoDataFrame(
        all_nuts2_gdf.merge(
            optimized_outputs["selected_portfolio"],
            on="nuts2_id",
            how="left",
        ),
        geometry="geometry",
        crs=all_nuts2_gdf.crs,
    )
    optimized_policy_map_gdf.to_file(DATA_PROCESSED_DIR / "nuts2_optimized_policy_map_data.geojson", driver="GeoJSON")

    plot_best_scenario_map(best_scenarios, countries_gdf, FIGURES_DIR / "best_scenario_map.png")
    plot_scenario_decomposition(summary, FIGURES_DIR / "eu_scenario_decomposition.png")
    plot_tradeoff_scatter(scenario_results, FIGURES_DIR / "country_tradeoff_scatter.png")
    plot_eu_uncertainty_ranges(sensitivity_outputs["eu_uncertainty_summary"], FIGURES_DIR / "eu_uncertainty_ranges.png")
    plot_country_robustness_heatmap(
        sensitivity_outputs["country_robustness"],
        FIGURES_DIR / "country_robustness_heatmap.png",
    )
    plot_robust_best_scenario_map(
        sensitivity_outputs["country_modal_scenario"],
        countries_gdf,
        FIGURES_DIR / "robust_best_scenario_map.png",
    )
    plot_nuts2_priority_map(nuts2_screening_map_gdf, FIGURES_DIR / "nuts2_priority_map.png")
    plot_nuts2_context_scatter(nuts2_screening_gdf, FIGURES_DIR / "nuts2_context_scatter.png")
    plot_integrated_policy_priority_map(
        selected_policies,
        all_nuts2_gdf[["nuts2_id", "geometry"]],
        FIGURES_DIR / "nuts2_integrated_policy_map.png",
    )
    plot_forest_food_tradeoff(selected_policies, FIGURES_DIR / "nuts2_forest_food_tradeoff.png")
    plot_integrated_policy_summary(policy_summary, FIGURES_DIR / "nuts2_integrated_policy_summary.png")
    plot_optimized_policy_map(
        optimized_outputs["selected_portfolio"],
        all_nuts2_gdf[["nuts2_id", "geometry"]],
        FIGURES_DIR / "nuts2_optimized_policy_map.png",
    )
    plot_optimized_portfolio_summary(
        optimized_outputs["policy_summary"],
        optimized_outputs["constraint_summary"],
        FIGURES_DIR / "nuts2_optimized_portfolio_summary.png",
    )
    plot_sweden_empirical_best_scenario_map(
        sweden_empirical_case["best_scenarios"],
        all_nuts2_gdf,
        FIGURES_DIR / "sweden_nuts2_empirical_best_scenario_map.png",
    )
    plot_sweden_empirical_comparison(
        sweden_comparison,
        FIGURES_DIR / "sweden_nuts2_empirical_comparison.png",
    )


def main() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ensure_directories()
    download_raw_data(force=False)
    baseline_inputs = build_baseline_inputs(year=ANALYSIS_YEAR)
    baseline_metrics = build_baseline_metrics(baseline_inputs)
    scenario_results = evaluate_scenarios(baseline_metrics)
    summary = summarize_scenarios(scenario_results)
    ranking = ranking_table(scenario_results)
    best_scenarios = best_scenario_by_country(scenario_results)
    sensitivity_outputs = run_sensitivity_analysis(baseline_inputs)
    countries_gdf = load_country_geometries()
    nuts2_screening_base_gdf = build_nuts2_screening_dataset(
        baseline_metrics=baseline_metrics,
        best_scenarios=best_scenarios,
        country_modal_scenario=sensitivity_outputs["country_modal_scenario"],
    )
    sweden_empirical_case = build_sweden_empirical_nuts2_case_study(
        baseline_inputs=baseline_inputs,
        reference_metrics=baseline_metrics,
    )
    sweden_comparison = compare_sweden_empirical_to_screening(
        nuts2_screening_base_gdf,
        empirical_baseline=sweden_empirical_case["baseline_metrics"],
        empirical_best=sweden_empirical_case["best_scenarios"],
    )
    nuts2_screening_gdf = build_nuts2_screening_dataset(
        baseline_metrics=baseline_metrics,
        best_scenarios=best_scenarios,
        country_modal_scenario=sensitivity_outputs["country_modal_scenario"],
        sweden_empirical_case=sweden_empirical_case,
    )
    all_nuts2_gdf = load_nuts2_geometries()
    nuts2_top_regions = top_nuts2_regions(nuts2_screening_gdf)
    policy_options = build_regional_policy_options(
        nuts2_screening_gdf,
        scenario_results,
        regional_scenario_results=sweden_empirical_case["scenario_results"],
    )
    selected_policies = select_regional_policy_priorities(policy_options)
    policy_summary = summarize_policy_priorities(selected_policies)
    switch_regions = policy_switch_regions(selected_policies)
    optimized_outputs = optimize_regional_policy_portfolio(policy_options, selected_policies)
    logger.info(
        "Optimized portfolio objective value: EUR %.2f bn",
        optimized_outputs["constraint_summary"]["portfolio_total_value_eur"].iloc[0] / 1_000_000_000.0,
    )
    _write_outputs(
        baseline_metrics=baseline_metrics,
        scenario_results=scenario_results,
        summary=summary,
        ranking=ranking,
        best_scenarios=best_scenarios,
        countries_gdf=countries_gdf,
        sensitivity_outputs=sensitivity_outputs,
        nuts2_screening_gdf=nuts2_screening_gdf,
        nuts2_top_regions=nuts2_top_regions,
        policy_options=policy_options,
        selected_policies=selected_policies,
        policy_summary=policy_summary,
        switch_regions=switch_regions,
        optimized_outputs=optimized_outputs,
        all_nuts2_gdf=all_nuts2_gdf,
        sweden_empirical_case=sweden_empirical_case,
        sweden_comparison=sweden_comparison,
    )


if __name__ == "__main__":
    main()
