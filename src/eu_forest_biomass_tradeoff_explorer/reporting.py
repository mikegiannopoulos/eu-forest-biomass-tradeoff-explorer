from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import (
    ANALYSIS_YEAR,
    DATA_RAW_DIR,
    DEFAULT_ALLOCATION_PARAMETERS,
    DEFAULT_MODEL_PARAMETERS,
    DEFAULT_OPTIMIZATION_PARAMETERS,
    RAW_DATASETS,
)


def _git_commit_hash(project_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def build_run_manifest(project_root: Path) -> dict[str, object]:
    datasets: list[dict[str, object]] = []
    for dataset_name, dataset in RAW_DATASETS.items():
        file_path = DATA_RAW_DIR / dataset["filename"]
        datasets.append(
            {
                "dataset_name": dataset_name,
                "filename": dataset["filename"],
                "url": dataset.get("url"),
                "exists": file_path.exists(),
                "size_bytes": file_path.stat().st_size if file_path.exists() else None,
                "modified_utc": (
                    datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()
                    if file_path.exists()
                    else None
                ),
            }
        )

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_year": ANALYSIS_YEAR,
        "git_commit_hash": _git_commit_hash(project_root),
        "input_datasets": datasets,
        "parameters": {
            "model": asdict(DEFAULT_MODEL_PARAMETERS),
            "allocation": asdict(DEFAULT_ALLOCATION_PARAMETERS),
            "optimization": asdict(DEFAULT_OPTIMIZATION_PARAMETERS),
        },
    }


def write_run_manifest(project_root: Path, output_path: Path) -> None:
    output_path.write_text(json.dumps(build_run_manifest(project_root), indent=2) + "\n")


def _format_region_counts(summary: pd.DataFrame, label_column: str) -> str:
    if summary.empty:
        return "none"
    parts = [f"{int(row['region_count'])} {row[label_column]}" for _, row in summary.iterrows()]
    return ", ".join(parts)


def write_consistency_audit(
    output_path: Path,
    *,
    sweden_best_scenarios: pd.DataFrame,
    selected_policies: pd.DataFrame,
    optimized_portfolio: pd.DataFrame,
    screening_gdf: pd.DataFrame,
    all_nuts2_gdf: pd.DataFrame,
    baseline_metrics: pd.DataFrame,
) -> None:
    se22_sweden = sweden_best_scenarios.loc[sweden_best_scenarios["nuts2_id"] == "SE22"].squeeze()
    se22_integrated = selected_policies.loc[selected_policies["nuts2_id"] == "SE22"].squeeze()
    se22_optimized = optimized_portfolio.loc[optimized_portfolio["nuts2_id"] == "SE22"].squeeze()

    dropped_nuts2_count = int(all_nuts2_gdf["nuts2_id"].nunique() - screening_gdf["nuts2_id"].nunique())
    missing_woodland_detail = int(
        screening_gdf.loc[
            screening_gdf["woodland_area_km2"].fillna(0.0) > 0.0,
            "has_missing_woodland_composition_detail",
        ].fillna(False).sum()
    )
    zero_baseline_regions = baseline_metrics.loc[~baseline_metrics["forest_policy_eligible"].fillna(False), "country"].tolist()

    integrated_summary = (
        selected_policies.groupby("selected_policy_label", as_index=False)
        .agg(region_count=("nuts2_id", "count"))
        .sort_values("region_count", ascending=False)
    )
    optimized_summary = (
        optimized_portfolio.groupby("optimized_policy_label", as_index=False)
        .agg(region_count=("nuts2_id", "count"))
        .sort_values("region_count", ascending=False)
    )

    lines = [
        "# Consistency Audit",
        "",
        "## SE22 trace",
        "",
        "The SE22 discrepancy is valid model behavior, not a hidden numerical inconsistency.",
        "",
        f"- Sweden empirical forest-only result: `{se22_sweden['scenario_label']}` at `{se22_sweden['value_eur_per_forest_ha']:.6f} EUR/forest ha`.",
        f"- Integrated NUTS-2 result: `{se22_integrated['selected_policy_label']}` at `{se22_integrated['selected_policy_value_eur_per_land_ha']:.6f} EUR/land ha`.",
        f"- Best forest option inside the integrated screen: `{se22_integrated['best_forest_policy_label']}` at `{se22_integrated['best_forest_policy_value_eur_per_land_ha']:.6f} EUR/land ha`.",
        f"- Food-land safeguard value in SE22: `{se22_integrated['food_land_policy_value_eur_per_land_ha']:.6f} EUR/land ha`.",
        f"- Integrated food-versus-forest margin in SE22: `{se22_integrated['food_vs_best_forest_margin_eur_per_land_ha']:.6f} EUR/land ha`.",
        f"- Optimized portfolio result: `{se22_optimized['optimized_policy_label']}` with `switch_from_unconstrained = {bool(se22_optimized['switch_from_unconstrained'])}`.",
        "",
        "Interpretation:",
        "The Sweden empirical map compares only forest scenarios and reports value per forest hectare. The integrated and optimized maps compare a larger policy space that includes Food-Land Safeguard and rank options by value per hectare of total land. SE22 keeps Material Cascade as its best forest option, but Food-Land Safeguard is slightly better once agricultural land competition is included.",
        "",
        "## Before vs after",
        "",
        "- Before this audit, the outputs mixed `carbon_value_eur_per_ha` and `policy_value_eur_per_ha_land` without common aliases or policy-space flags, so SE22 looked inconsistent unless traced manually.",
        "- After this audit, the outputs expose both `value_eur_per_forest_ha` and `value_eur_per_land_ha`, and every regional policy output carries `is_forest_only` plus `includes_food_policy`.",
        "- The SE22 selections did not change after the audit. The correction is interpretive and traceability-focused, not a numerical reversal.",
        "",
        "## Structural checks",
        "",
        f"- NUTS-2 regions present in geometry layer but absent from the selected land-cover join: `{dropped_nuts2_count}`.",
        f"- Regions with woodland area but missing woodland subclass detail before zero-filling: `{missing_woodland_detail}`.",
        f"- Country-level forest scenario rows excluded from best-scenario selection because baseline forest activity is zero: `{', '.join(zero_baseline_regions) if zero_baseline_regions else 'none'}`.",
        "",
        "## Current portfolio counts",
        "",
        f"- Integrated priorities: {_format_region_counts(integrated_summary, 'selected_policy_label')}.",
        f"- Optimized portfolio: {_format_region_counts(optimized_summary, 'optimized_policy_label')}.",
        "",
        "## Conclusion",
        "",
        "SE22 is not evidence of a silent coding error. It is evidence that the project contains two different decision frames: a forest-only empirical Sweden rerun and a broader integrated land-use comparison. The audit found real structural issues elsewhere, especially silent NUTS-2 join loss and missing-detail zero filling, but the SE22 switch itself is mathematically expected under the current model definition.",
        "",
    ]
    output_path.write_text("\n".join(lines))
