from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .allocation import FOOD_LAND_POLICY_NAME
from .config import DEFAULT_OPTIMIZATION_PARAMETERS, OptimizationParameters

logger = logging.getLogger(__name__)


def _load_solver():
    try:
        from scipy.optimize import Bounds, LinearConstraint, milp
    except ImportError as exc:
        raise ImportError(
            "scipy is required for the constrained policy allocation step. "
            "Install project dependencies in the repo-local .venv before running the pipeline."
        ) from exc
    return Bounds, LinearConstraint, milp


def _constraint_metric_row(
    *,
    constraint: str,
    units: str,
    reference_total: float,
    minimum_required: float,
    achieved: float,
    portfolio_total_value_eur: float,
    switch_count: int,
    switch_share: float,
    solver_status: int,
    solver_message: str,
) -> dict[str, float | int | str]:
    required_share_of_reference = minimum_required / reference_total if reference_total > 0.0 else 0.0
    achieved_share_of_reference = achieved / reference_total if reference_total > 0.0 else 0.0
    achieved_share_of_requirement = achieved / minimum_required if minimum_required > 0.0 else 0.0
    delta_from_required = achieved - minimum_required
    delta_share_of_reference = achieved_share_of_reference - required_share_of_reference
    delta_share_of_requirement = achieved_share_of_requirement - 1.0 if minimum_required > 0.0 else 0.0
    return {
        "constraint": constraint,
        "units": units,
        "reference_total": reference_total,
        "minimum_required": minimum_required,
        "achieved": achieved,
        "required_share_of_reference": required_share_of_reference,
        "achieved_share_of_reference": achieved_share_of_reference,
        "achieved_share_of_requirement": achieved_share_of_requirement,
        "delta_from_required": delta_from_required,
        "delta_share_of_reference": delta_share_of_reference,
        "delta_share_of_requirement": delta_share_of_requirement,
        "portfolio_total_value_eur": portfolio_total_value_eur,
        "switch_count": switch_count,
        "switch_share": switch_share,
        "solver_status": solver_status,
        "solver_message": solver_message,
    }


def compute_constraint_metrics(
    *,
    total_baseline_harvest_m3: float,
    minimum_harvest_m3: float,
    achieved_harvest_m3: float,
    total_food_capacity_indexed_ha: float,
    minimum_food_capacity_indexed_ha: float,
    achieved_food_capacity_indexed_ha: float,
    total_value_eur: float,
    switch_count: int,
    switch_share: float,
    solver_status: int,
    solver_message: str,
) -> pd.DataFrame:
    constraint_summary = pd.DataFrame(
        [
            _constraint_metric_row(
                constraint="Biomass supply floor",
                units="m3",
                reference_total=total_baseline_harvest_m3,
                minimum_required=minimum_harvest_m3,
                achieved=achieved_harvest_m3,
                portfolio_total_value_eur=total_value_eur,
                switch_count=switch_count,
                switch_share=switch_share,
                solver_status=solver_status,
                solver_message=solver_message,
            ),
            _constraint_metric_row(
                constraint="Food-capacity safeguard floor",
                units="indexed_ha",
                reference_total=total_food_capacity_indexed_ha,
                minimum_required=minimum_food_capacity_indexed_ha,
                achieved=achieved_food_capacity_indexed_ha,
                portfolio_total_value_eur=total_value_eur,
                switch_count=switch_count,
                switch_share=switch_share,
                solver_status=solver_status,
                solver_message=solver_message,
            ),
        ]
    )
    validate_constraint_metrics(constraint_summary)
    return constraint_summary


def validate_constraint_metrics(constraint_summary: pd.DataFrame) -> None:
    required_columns = [
        "reference_total",
        "minimum_required",
        "achieved",
        "required_share_of_reference",
        "achieved_share_of_reference",
        "achieved_share_of_requirement",
        "delta_from_required",
        "delta_share_of_reference",
        "delta_share_of_requirement",
    ]
    missing = [column for column in required_columns if column not in constraint_summary.columns]
    if missing:
        raise ValueError(f"Constraint summary is missing required columns: {', '.join(missing)}")

    for row in constraint_summary.itertuples(index=False):
        expected_required_share = row.minimum_required / row.reference_total if row.reference_total > 0.0 else 0.0
        expected_achieved_share = row.achieved / row.reference_total if row.reference_total > 0.0 else 0.0
        expected_ratio = row.achieved / row.minimum_required if row.minimum_required > 0.0 else 0.0
        expected_delta = row.achieved - row.minimum_required
        if not np.isclose(row.required_share_of_reference, expected_required_share):
            raise AssertionError(f"{row.constraint}: required_share_of_reference is inconsistent with raw totals.")
        if not np.isclose(row.achieved_share_of_reference, expected_achieved_share):
            raise AssertionError(f"{row.constraint}: achieved_share_of_reference is inconsistent with raw totals.")
        if not np.isclose(row.achieved_share_of_requirement, expected_ratio):
            raise AssertionError(f"{row.constraint}: achieved_share_of_requirement is inconsistent with raw totals.")
        if not np.isclose(row.delta_from_required, expected_delta):
            raise AssertionError(f"{row.constraint}: delta_from_required is inconsistent with raw totals.")
        if not np.isclose(row.delta_share_of_reference, row.achieved_share_of_reference - row.required_share_of_reference):
            raise AssertionError(f"{row.constraint}: delta_share_of_reference is internally inconsistent.")
        if not np.isclose(row.delta_share_of_requirement, row.achieved_share_of_requirement - 1.0):
            raise AssertionError(f"{row.constraint}: delta_share_of_requirement is internally inconsistent.")


def constraint_debug_lines(constraint_summary: pd.DataFrame) -> list[str]:
    validate_constraint_metrics(constraint_summary)
    lines: list[str] = []
    for row in constraint_summary.itertuples(index=False):
        lines.append(
            f"{row.constraint}: reference_total={row.reference_total:.6g} {row.units}, "
            f"minimum_required={row.minimum_required:.6g} {row.units}, "
            f"achieved={row.achieved:.6g} {row.units}, "
            f"achieved/reference={row.achieved_share_of_reference:.4f}, "
            f"achieved/required={row.achieved_share_of_requirement:.4f}, "
            f"delta={row.delta_from_required:.6g} {row.units}"
        )
    return lines


def optimize_regional_policy_portfolio(
    policy_options: pd.DataFrame,
    unconstrained_priorities: pd.DataFrame,
    parameters: OptimizationParameters = DEFAULT_OPTIMIZATION_PARAMETERS,
) -> dict[str, pd.DataFrame]:
    Bounds, LinearConstraint, milp = _load_solver()

    options = policy_options.sort_values(["nuts2_id", "scenario_label"]).reset_index(drop=True).copy()
    option_count = len(options)
    if option_count == 0:
        raise ValueError("Policy options are empty; cannot solve constrained portfolio.")

    option_counts_by_region = options.groupby("nuts2_id")["scenario"].nunique()
    if (option_counts_by_region < 2).any():
        incomplete = ", ".join(option_counts_by_region.loc[option_counts_by_region < 2].index.tolist()[:10])
        raise ValueError(f"Some regions do not have a usable policy option set: {incomplete}")

    objective = -options["policy_value_eur"].fillna(0.0).to_numpy(dtype=float)
    integrality = np.ones(option_count, dtype=int)
    bounds = Bounds(np.zeros(option_count), np.ones(option_count))

    constraint_rows: list[np.ndarray] = []
    lower_bounds: list[float] = []
    upper_bounds: list[float] = []

    for _, index in options.groupby("nuts2_id").indices.items():
        row = np.zeros(option_count, dtype=float)
        row[index] = 1.0
        constraint_rows.append(row)
        lower_bounds.append(1.0)
        upper_bounds.append(1.0)

    total_baseline_harvest_m3 = (
        options.groupby("nuts2_id", as_index=False)["regional_baseline_harvest_m3"].first()["regional_baseline_harvest_m3"].sum()
    )
    minimum_harvest_m3 = total_baseline_harvest_m3 * parameters.biomass_supply_floor_share
    constraint_rows.append(options["regional_harvest_after_policy_m3"].fillna(0.0).to_numpy(dtype=float))
    lower_bounds.append(minimum_harvest_m3)
    upper_bounds.append(np.inf)

    total_food_capacity_indexed_ha = options.loc[
        options["scenario"] == FOOD_LAND_POLICY_NAME,
        "food_capacity_indexed_ha",
    ].fillna(0.0).sum()
    minimum_food_capacity_indexed_ha = total_food_capacity_indexed_ha * parameters.food_capacity_floor_share
    constraint_rows.append(options["food_capacity_indexed_ha"].fillna(0.0).to_numpy(dtype=float))
    lower_bounds.append(minimum_food_capacity_indexed_ha)
    upper_bounds.append(np.inf)

    result = milp(
        c=objective,
        constraints=LinearConstraint(
            np.vstack(constraint_rows),
            np.array(lower_bounds, dtype=float),
            np.array(upper_bounds, dtype=float),
        ),
        integrality=integrality,
        bounds=bounds,
    )
    if not result.success:
        raise RuntimeError(f"Optimization did not converge: {result.message}")

    options["selected"] = result.x > 0.5
    selected = options.loc[options["selected"]].copy()
    if len(selected) != options["nuts2_id"].nunique():
        raise RuntimeError("Optimization result does not select exactly one option per region.")

    unconstrained_lookup = unconstrained_priorities[
        [
            "nuts2_id",
            "selected_policy",
            "selected_policy_label",
            "selected_policy_value_eur_per_ha_land",
            "selected_policy_value_eur_per_land_ha",
        ]
    ].copy()
    selected = selected.merge(unconstrained_lookup, on="nuts2_id", how="left")
    selected["switch_from_unconstrained"] = selected["scenario"] != selected["selected_policy"]
    selected["optimized_minus_unconstrained_value_eur_per_ha_land"] = (
        selected["policy_value_eur_per_ha_land"] - selected["selected_policy_value_eur_per_ha_land"]
    )
    selected["optimized_minus_unconstrained_value_eur_per_land_ha"] = (
        selected["value_eur_per_land_ha"] - selected["selected_policy_value_eur_per_land_ha"]
    )

    selected = selected.rename(
        columns={
            "scenario": "optimized_policy",
            "scenario_label": "optimized_policy_label",
            "scenario_description": "optimized_policy_description",
            "option_type": "optimized_policy_type",
            "marginal_target_area_ha": "optimized_target_area_ha",
            "marginal_cropland_target_area_ha": "optimized_target_cropland_area_ha",
            "changed_harvest_m3": "optimized_policy_changed_harvest_m3",
            "delta_biodiversity_pressure_proxy": "optimized_policy_delta_biodiversity_pressure_proxy",
            "food_land_displacement_proxy_tco2e_per_ha": "optimized_food_land_proxy_tco2e_per_ha",
            "food_capacity_indexed_ha": "optimized_food_capacity_indexed_ha",
            "estimated_policy_benefit_tco2e": "optimized_policy_benefit_tco2e",
            "policy_benefit_tco2e_per_ha_land": "optimized_policy_benefit_tco2e_per_ha_land",
            "policy_value_eur": "optimized_policy_value_eur",
            "policy_value_eur_per_ha_land": "optimized_policy_value_eur_per_ha_land",
            "benefit_tco2e_per_land_ha": "optimized_policy_benefit_tco2e_per_land_ha",
            "value_eur_per_land_ha": "optimized_policy_value_eur_per_land_ha",
            "benefit_tco2e_per_forest_ha": "optimized_policy_benefit_tco2e_per_forest_ha",
            "value_eur_per_forest_ha": "optimized_policy_value_eur_per_forest_ha",
            "regional_harvest_after_policy_m3": "optimized_regional_harvest_after_policy_m3",
            "regional_harvest_change_m3": "optimized_regional_harvest_change_m3",
        }
    ).drop(columns="selected")
    selected["is_forest_only"] = False
    selected["includes_food_policy"] = True

    policy_summary = (
        selected.groupby(["optimized_policy", "optimized_policy_label"], as_index=False)
        .agg(
            region_count=("nuts2_id", "count"),
            optimized_policy_value_eur=("optimized_policy_value_eur", "sum"),
            optimized_policy_benefit_tco2e=("optimized_policy_benefit_tco2e", "sum"),
            optimized_regional_harvest_after_policy_m3=("optimized_regional_harvest_after_policy_m3", "sum"),
            optimized_food_capacity_indexed_ha=("optimized_food_capacity_indexed_ha", "sum"),
            switch_from_unconstrained_count=("switch_from_unconstrained", "sum"),
        )
        .sort_values("optimized_policy_value_eur", ascending=False)
        .reset_index(drop=True)
    )
    policy_summary["mean_value_eur_per_region"] = policy_summary["optimized_policy_value_eur"] / policy_summary["region_count"]

    achieved_harvest_m3 = selected["optimized_regional_harvest_after_policy_m3"].sum()
    achieved_food_capacity_indexed_ha = selected["optimized_food_capacity_indexed_ha"].sum()
    total_value_eur = selected["optimized_policy_value_eur"].sum()
    switch_count = int(selected["switch_from_unconstrained"].sum())
    switch_share = switch_count / len(selected)

    constraint_summary = compute_constraint_metrics(
        total_baseline_harvest_m3=total_baseline_harvest_m3,
        minimum_harvest_m3=minimum_harvest_m3,
        achieved_harvest_m3=achieved_harvest_m3,
        total_food_capacity_indexed_ha=total_food_capacity_indexed_ha,
        minimum_food_capacity_indexed_ha=minimum_food_capacity_indexed_ha,
        achieved_food_capacity_indexed_ha=achieved_food_capacity_indexed_ha,
        total_value_eur=total_value_eur,
        switch_count=switch_count,
        switch_share=switch_share,
        solver_status=result.status,
        solver_message=result.message,
    )
    for line in constraint_debug_lines(constraint_summary):
        logger.info(line)

    switch_regions = selected.loc[selected["switch_from_unconstrained"]].copy()
    switch_regions = switch_regions.sort_values(
        "optimized_minus_unconstrained_value_eur_per_ha_land",
        ascending=True,
    ).reset_index(drop=True)

    return {
        "selected_portfolio": selected.sort_values(["country", "nuts2_name"]).reset_index(drop=True),
        "policy_summary": policy_summary,
        "constraint_summary": constraint_summary,
        "switch_regions": switch_regions,
    }
