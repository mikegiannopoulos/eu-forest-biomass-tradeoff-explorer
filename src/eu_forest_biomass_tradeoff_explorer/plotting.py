from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
from matplotlib import colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd

from .allocation import FOOD_LAND_POLICY_LABEL

SCENARIO_COLORS = {
    "Conservation Priority": "#2f6b3b",
    "Material Cascade": "#c2781c",
    "Bioenergy Push": "#9d1f16",
    FOOD_LAND_POLICY_LABEL: "#225ea8",
}
SCENARIO_ORDER = ["Conservation Priority", "Material Cascade", "Bioenergy Push"]
PRIORITY_ORDER = ["Conservation Priority", "Material Cascade", FOOD_LAND_POLICY_LABEL, "Bioenergy Push"]
EUROPE_XLIM = (-11.5, 36.5)
EUROPE_YLIM = (34.0, 72.5)
DISPLAY_LABELS = {
    "Conservation Priority": "Conservation\nPriority",
    "Material Cascade": "Material\nCascade",
    "Bioenergy Push": "Bioenergy\nPush",
    FOOD_LAND_POLICY_LABEL: "Food-Land\nSafeguard",
}


def _save_figure(path: Path) -> None:
    fig = plt.gcf()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not fig.get_constrained_layout():
        fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def _set_europe_extent(ax) -> None:
    ax.set_xlim(*EUROPE_XLIM)
    ax.set_ylim(*EUROPE_YLIM)


def _set_bounds_with_padding(ax, gdf: gpd.GeoDataFrame, padding_share: float = 0.06) -> None:
    minx, miny, maxx, maxy = gdf.total_bounds
    xrange = maxx - minx
    yrange = maxy - miny
    ax.set_xlim(minx - xrange * padding_share, maxx + xrange * padding_share)
    ax.set_ylim(miny - yrange * padding_share, maxy + yrange * padding_share)


def _hide_map_axes(ax) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.axis("off")


def _annotate_points(ax, rows: pd.DataFrame, x_col: str, y_col: str, label_col: str, fontsize: int = 8) -> None:
    offsets = [(4, 4), (4, -10), (-18, 4), (-18, -10), (10, 8), (10, -14), (-24, 8), (-24, -14)]
    for index, (_, row) in enumerate(rows.iterrows()):
        dx, dy = offsets[index % len(offsets)]
        ax.annotate(
            row[label_col],
            (row[x_col], row[y_col]),
            fontsize=fontsize,
            xytext=(dx, dy),
            textcoords="offset points",
        )


def _display_label(label: str) -> str:
    return DISPLAY_LABELS.get(label, label)


def _optimized_constraint_plot_metrics(constraint_summary: pd.DataFrame) -> pd.DataFrame:
    constraints = constraint_summary.copy()
    constraints["achieved_ratio_label"] = constraints["achieved_share_of_requirement"].map(
        lambda value: f"{value:.2f}× ({value:.0%})"
    )
    constraints["delta_ratio_label"] = constraints["delta_share_of_requirement"].map(lambda value: f"{value:+.2f}")
    return constraints


def plot_best_scenario_map(best_scenarios: pd.DataFrame, countries_gdf: gpd.GeoDataFrame, output_path: Path) -> None:
    plot_df = countries_gdf.merge(
        best_scenarios[["country", "scenario_label", "carbon_value_eur_per_ha"]],
        on="country",
        how="left",
    )
    plot_df["plot_color"] = plot_df["scenario_label"].map(SCENARIO_COLORS).fillna("#d9d9d9")

    fig, ax = plt.subplots(figsize=(11, 8))
    plot_df.plot(color=plot_df["plot_color"], edgecolor="white", linewidth=0.4, ax=ax)
    projected = plot_df.to_crs(3035)
    plot_df["area_km2"] = projected.geometry.area / 1_000_000.0
    small = plot_df.loc[plot_df["area_km2"] < 20_000.0].copy()
    small_points = small.representative_point()
    ax.scatter(
        small_points.x,
        small_points.y,
        s=32,
        c=small["plot_color"],
        edgecolors="#222222",
        linewidths=0.5,
        zorder=4,
    )
    ax.set_title("Best-performing EU forest biomass scenario at EUR 100/tCO2", fontsize=14, pad=12)
    _set_europe_extent(ax)
    _hide_map_axes(ax)

    legend_handles = [
        plt.Line2D([0], [0], marker="s", linestyle="", color=color, markersize=10, label=label)
        for label, color in SCENARIO_COLORS.items()
        if label in SCENARIO_ORDER
    ]
    legend_handles.append(
        plt.Line2D([0], [0], marker="o", linestyle="", color="#666666", markerfacecolor="#bbbbbb", markersize=6, label="Small-country marker")
    )
    ax.legend(handles=legend_handles, frameon=False, loc="center left", bbox_to_anchor=(1.02, 0.5))
    _save_figure(output_path)


def plot_scenario_decomposition(summary_df: pd.DataFrame, output_path: Path) -> None:
    summary = summary_df.loc[summary_df["scenario"] != "baseline"].copy()
    summary["scenario_label"] = pd.Categorical(summary["scenario_label"], categories=SCENARIO_ORDER, ordered=True)
    summary = summary.sort_values("scenario_label")
    labels = summary["scenario_label"].tolist()
    display_labels = [_display_label(label) for label in labels]
    x = list(range(len(labels)))

    fig, (ax_net, ax_components) = plt.subplots(
        1,
        2,
        figsize=(13, 5.8),
        gridspec_kw={"width_ratios": [0.9, 1.3]},
        constrained_layout=True,
    )

    net_values = summary["net_climate_benefit_tco2e"].to_numpy() / 1_000_000.0
    net_colors = [SCENARIO_COLORS[label] for label in labels]
    ax_net.bar(display_labels, net_values, color=net_colors)
    ax_net.axhline(0.0, color="#333333", linewidth=0.8)
    ax_net.set_ylabel("Net climate benefit relative to baseline (MtCO2e)")
    ax_net.set_title("A. Overall EU result")
    for xpos, value in zip(x, net_values, strict=False):
        va = "bottom" if value >= 0 else "top"
        offset = 0.45 if value >= 0 else -0.45
        ax_net.text(xpos, value + offset, f"{value:.1f}", ha="center", va=va, fontsize=9)
    ax_net.set_xticks(x, display_labels)

    component_specs = [
        ("Forest carbon retention", "forest_carbon_retention_tco2e", "#4f772d"),
        ("Substitution gain", "substitution_gain_tco2e", "#f4a259"),
        ("Supply-chain savings", "supply_chain_savings_tco2e", "#3d5a80"),
    ]
    width = 0.22
    offsets = [-width, 0.0, width]
    for offset, (label, column, color) in zip(offsets, component_specs, strict=False):
        values = summary[column].to_numpy() / 1_000_000.0
        ax_components.bar([value + offset for value in x], values, width=width, color=color, label=label)
    ax_components.axhline(0.0, color="#333333", linewidth=0.8)
    ax_components.set_xticks(x, display_labels)
    ax_components.set_ylabel("Component contribution (MtCO2e)")
    ax_components.set_title("B. What drives the result")
    handles, legend_labels = ax_components.get_legend_handles_labels()
    fig.legend(handles, legend_labels, frameon=False, loc="outside upper center", ncol=3)
    ax_components.text(
        0.02,
        0.02,
        "Positive bars help climate relative to baseline.\nNegative bars work against the scenario.",
        transform=ax_components.transAxes,
        fontsize=8,
    )
    _save_figure(output_path)


def plot_tradeoff_scatter(scenario_results: pd.DataFrame, output_path: Path) -> None:
    plot_df = scenario_results.loc[scenario_results["scenario"] != "baseline"].copy()

    fig, ax = plt.subplots(figsize=(10, 6))
    for scenario_label, group in plot_df.groupby("scenario_label"):
        ax.scatter(
            group["biodiversity_pressure_proxy"],
            group["net_climate_benefit_tco2e_per_ha"],
            s=45,
            alpha=0.8,
            label=scenario_label,
            color=SCENARIO_COLORS[scenario_label],
        )

    annotate = (
        plot_df.sort_values("net_climate_benefit_tco2e_per_ha", ascending=False)
        .groupby("scenario_label")
        .head(3)
    )
    _annotate_points(
        ax,
        annotate,
        x_col="biodiversity_pressure_proxy",
        y_col="net_climate_benefit_tco2e_per_ha",
        label_col="country",
    )

    ax.axhline(0.0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Biodiversity-pressure proxy (harvest intensity x naturally regenerating share)")
    ax.set_ylabel("Net climate benefit relative to baseline (tCO2e/ha)")
    ax.set_title("Country-level climate and ecological pressure trade-offs")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1.0))
    ax.margins(x=0.03, y=0.08)
    _save_figure(output_path)


def plot_eu_uncertainty_ranges(eu_uncertainty_summary: pd.DataFrame, output_path: Path) -> None:
    summary = eu_uncertainty_summary.copy()
    summary["scenario_label"] = pd.Categorical(summary["scenario_label"], categories=SCENARIO_ORDER, ordered=True)
    summary = summary.sort_values("scenario_label")

    fig, ax = plt.subplots(figsize=(10, 6))
    x_positions = range(len(summary))
    medians = summary["median_net_climate_benefit_tco2e"] / 1_000_000.0
    lower = (summary["median_net_climate_benefit_tco2e"] - summary["p10_net_climate_benefit_tco2e"]) / 1_000_000.0
    upper = (summary["p90_net_climate_benefit_tco2e"] - summary["median_net_climate_benefit_tco2e"]) / 1_000_000.0

    for x_position, (_, row) in zip(x_positions, summary.iterrows(), strict=False):
        ax.errorbar(
            x_position,
            row["median_net_climate_benefit_tco2e"] / 1_000_000.0,
            yerr=[
                [(row["median_net_climate_benefit_tco2e"] - row["p10_net_climate_benefit_tco2e"]) / 1_000_000.0],
                [(row["p90_net_climate_benefit_tco2e"] - row["median_net_climate_benefit_tco2e"]) / 1_000_000.0],
            ],
            fmt="o",
            color=SCENARIO_COLORS[row["scenario_label"]],
            capsize=6,
            linewidth=2,
            markersize=7,
        )
        ax.scatter(
            x_position,
            row["mean_net_climate_benefit_tco2e"] / 1_000_000.0,
            marker="D",
            color="black",
            s=28,
            zorder=4,
        )

    ax.axhline(0.0, color="#333333", linewidth=0.8)
    ax.set_xticks(list(x_positions), summary["scenario_label"].tolist(), rotation=0)
    ax.set_ylabel("EU net climate benefit relative to baseline (MtCO2e)")
    ax.set_title("EU scenario uncertainty ranges across sensitivity runs")
    ax.text(0.02, 0.02, "Circle = median, diamond = mean, whiskers = p10-p90", transform=ax.transAxes, fontsize=8)
    _save_figure(output_path)


def plot_country_robustness_heatmap(country_robustness: pd.DataFrame, output_path: Path) -> None:
    heatmap_df = country_robustness.pivot(index="country", columns="scenario_label", values="share_best").fillna(0.0)
    available_columns = [column for column in SCENARIO_ORDER if column in heatmap_df.columns]
    heatmap_df = heatmap_df[available_columns]
    heatmap_df = heatmap_df.loc[heatmap_df.max(axis=1).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(9, 10))
    im = ax.imshow(heatmap_df.to_numpy(), aspect="auto", cmap="YlGn", vmin=0.0, vmax=1.0)
    ax.set_xticks(range(len(heatmap_df.columns)), heatmap_df.columns, rotation=25, ha="right")
    ax.set_yticks(range(len(heatmap_df.index)), heatmap_df.index)
    ax.set_title("Country-level scenario robustness across sensitivity runs")

    for row_index, country in enumerate(heatmap_df.index):
        for col_index, scenario in enumerate(heatmap_df.columns):
            value = heatmap_df.loc[country, scenario]
            ax.text(
                col_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=7,
                color="black" if value < 0.65 else "white",
            )

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Share of sensitivity runs where the scenario is best")
    _save_figure(output_path)


def plot_robust_best_scenario_map(
    country_modal_scenario: pd.DataFrame,
    countries_gdf: gpd.GeoDataFrame,
    output_path: Path,
) -> None:
    plot_df = countries_gdf.merge(
        country_modal_scenario[["country", "scenario_label", "share_best"]],
        on="country",
        how="left",
    )

    plot_colors = []
    for _, row in plot_df.iterrows():
        color = SCENARIO_COLORS.get(row["scenario_label"], "#d9d9d9")
        alpha = 0.25 + 0.75 * float(row["share_best"] if pd.notna(row["share_best"]) else 0.0)
        plot_colors.append(mcolors.to_rgba(color, alpha=alpha))

    fig, ax = plt.subplots(figsize=(11, 8))
    plot_df.plot(color=plot_colors, edgecolor="white", linewidth=0.4, ax=ax)
    ax.set_title("Modal best EU scenario under sensitivity analysis\nOpacity indicates robustness", fontsize=14, pad=12)
    _set_europe_extent(ax)
    _hide_map_axes(ax)

    legend_handles = [
        plt.Line2D([0], [0], marker="s", linestyle="", color=color, markersize=10, label=label)
        for label, color in SCENARIO_COLORS.items()
    ]
    ax.legend(handles=legend_handles, frameon=False, loc="center left", bbox_to_anchor=(1.02, 0.5))
    _save_figure(output_path)


def plot_nuts2_priority_map(nuts2_gdf: gpd.GeoDataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 8))
    nuts2_gdf.plot(
        column="screening_priority_score",
        cmap="YlGnBu",
        linewidth=0.1,
        edgecolor="white",
        legend=True,
        ax=ax,
        missing_kwds={"color": "#f0f0f0"},
    )
    ax.set_title(
        "NUTS-2 screening priority score\n(best scenario value x woodland share x country-level robustness)",
        fontsize=14,
        pad=12,
    )
    _set_europe_extent(ax)
    _hide_map_axes(ax)
    _save_figure(output_path)


def plot_nuts2_context_scatter(nuts2_gdf: gpd.GeoDataFrame, output_path: Path) -> None:
    plot_df = nuts2_gdf.copy()
    fig, ax = plt.subplots(figsize=(10, 6))

    for scenario_label, group in plot_df.groupby("modal_scenario_label"):
        ax.scatter(
            group["woodland_share_of_land"],
            group["screening_priority_score"],
            s=28,
            alpha=0.7,
            color=SCENARIO_COLORS.get(scenario_label, "#777777"),
            label=scenario_label,
        )

    annotate = plot_df.sort_values("screening_priority_score", ascending=False).head(2)
    _annotate_points(
        ax,
        annotate,
        x_col="woodland_share_of_land",
        y_col="screening_priority_score",
        label_col="nuts2_id",
    )

    ax.set_xlabel("Woodland share of total land")
    ax.set_ylabel("NUTS-2 screening priority score")
    ax.set_title("Regional woodland context and NUTS-2 screening priority")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1.0))
    ax.margins(x=0.03, y=0.08)
    _save_figure(output_path)


def plot_integrated_policy_priority_map(
    selected_policies: pd.DataFrame,
    nuts2_gdf: gpd.GeoDataFrame,
    output_path: Path,
) -> None:
    plot_df = nuts2_gdf.merge(
        selected_policies[["nuts2_id", "selected_policy_label"]],
        on="nuts2_id",
        how="left",
    )
    plot_df["plot_color"] = plot_df["selected_policy_label"].map(SCENARIO_COLORS).fillna("#d9d9d9")

    fig, ax = plt.subplots(figsize=(11, 8))
    plot_df.plot(color=plot_df["plot_color"], edgecolor="white", linewidth=0.1, ax=ax)
    ax.set_title(
        "Integrated NUTS-2 land-use priority\nforest carbon options versus food-land safeguard (EUR/ha of total land)",
        fontsize=14,
        pad=12,
    )
    _set_europe_extent(ax)
    _hide_map_axes(ax)

    legend_handles = [
        plt.Line2D([0], [0], marker="s", linestyle="", color=SCENARIO_COLORS[label], markersize=10, label=label)
        for label in PRIORITY_ORDER
        if label in plot_df["selected_policy_label"].dropna().unique()
    ]
    if plot_df["selected_policy_label"].isna().any():
        legend_handles.append(
            plt.Line2D([0], [0], marker="s", linestyle="", color="#d9d9d9", markersize=10, label="No data")
        )
    ax.legend(handles=legend_handles, frameon=False, loc="center left", bbox_to_anchor=(1.02, 0.5))
    fig.text(0.02, 0.02, "Grey regions = no matching NUTS-2 land-cover data in the selected Eurostat layer", fontsize=8)
    _save_figure(output_path)


def plot_forest_food_tradeoff(selected_policies: pd.DataFrame, output_path: Path) -> None:
    plot_df = selected_policies.copy()
    fig, ax = plt.subplots(figsize=(10, 6))

    for policy_label, group in plot_df.groupby("selected_policy_label"):
        ax.scatter(
            group["best_forest_policy_value_eur_per_ha_land"],
            group["food_land_policy_value_eur_per_ha_land"],
            s=28,
            alpha=0.75,
            color=SCENARIO_COLORS.get(policy_label, "#777777"),
            label=policy_label,
        )

    max_value = max(
        float(plot_df["best_forest_policy_value_eur_per_ha_land"].max()),
        float(plot_df["food_land_policy_value_eur_per_ha_land"].max()),
    )
    ax.plot([0.0, max_value], [0.0, max_value], color="#333333", linewidth=1.0, linestyle="--")

    annotate = (
        plot_df.loc[plot_df["switch_from_best_forest"]]
        .sort_values("food_vs_best_forest_margin_eur_per_ha_land", ascending=False)
        .head(3)
    )
    _annotate_points(
        ax,
        annotate,
        x_col="best_forest_policy_value_eur_per_ha_land",
        y_col="food_land_policy_value_eur_per_ha_land",
        label_col="nuts2_id",
    )

    ax.set_xlabel("Best forest-option value (EUR/ha of total land)")
    ax.set_ylabel("Food-land safeguard value (EUR/ha of total land)")
    ax.set_title("Regional forest-versus-food trade-off screening")
    ax.text(0.02, 0.02, "Dashed line = equal policy value", transform=ax.transAxes, fontsize=8)
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1.0))
    ax.margins(x=0.03, y=0.08)
    _save_figure(output_path)


def plot_integrated_policy_summary(summary_df: pd.DataFrame, output_path: Path) -> None:
    summary = summary_df.copy()
    summary["selected_policy_label"] = pd.Categorical(
        summary["selected_policy_label"],
        categories=PRIORITY_ORDER,
        ordered=True,
    )
    summary = summary.sort_values("selected_policy_label")

    fig, ax = plt.subplots(figsize=(9, 5))
    values = summary["selected_policy_value_eur"] / 1_000_000.0
    colors = [SCENARIO_COLORS.get(label, "#777777") for label in summary["selected_policy_label"]]
    ax.bar(summary["selected_policy_label"], values, color=colors)

    for _, row in summary.iterrows():
        ax.text(
            row["selected_policy_label"],
            row["selected_policy_value_eur"] / 1_000_000.0 + 0.5,
            f"{int(row['region_count'])} regions",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    ax.set_ylabel("Aggregate selected policy value (million EUR)")
    ax.set_title("Integrated NUTS-2 policy portfolio summary")
    _save_figure(output_path)


def plot_optimized_policy_map(
    optimized_portfolio: pd.DataFrame,
    nuts2_gdf: gpd.GeoDataFrame,
    output_path: Path,
) -> None:
    plot_df = nuts2_gdf.merge(
        optimized_portfolio[["nuts2_id", "optimized_policy_label"]],
        on="nuts2_id",
        how="left",
    )
    plot_df["plot_color"] = plot_df["optimized_policy_label"].map(SCENARIO_COLORS).fillna("#d9d9d9")

    fig, ax = plt.subplots(figsize=(11, 8))
    plot_df.plot(color=plot_df["plot_color"], edgecolor="white", linewidth=0.1, ax=ax)
    ax.set_title(
        "Constrained NUTS-2 policy portfolio\nmax value (EUR/ha of total land) with biomass-supply and food-capacity safeguards",
        fontsize=14,
        pad=12,
    )
    _set_europe_extent(ax)
    _hide_map_axes(ax)

    legend_handles = [
        plt.Line2D([0], [0], marker="s", linestyle="", color=SCENARIO_COLORS[label], markersize=10, label=label)
        for label in PRIORITY_ORDER
        if label in plot_df["optimized_policy_label"].dropna().unique()
    ]
    if plot_df["optimized_policy_label"].isna().any():
        legend_handles.append(
            plt.Line2D([0], [0], marker="s", linestyle="", color="#d9d9d9", markersize=10, label="No data")
        )
    ax.legend(handles=legend_handles, frameon=False, loc="center left", bbox_to_anchor=(1.02, 0.5))
    fig.text(0.02, 0.02, "Grey regions = no matching NUTS-2 land-cover data in the selected Eurostat layer", fontsize=8)
    _save_figure(output_path)


def plot_optimized_portfolio_summary(
    policy_summary: pd.DataFrame,
    constraint_summary: pd.DataFrame,
    output_path: Path,
) -> None:
    summary = policy_summary.copy()
    summary["optimized_policy_label"] = pd.Categorical(
        summary["optimized_policy_label"],
        categories=PRIORITY_ORDER,
        ordered=True,
    )
    summary = summary.sort_values("optimized_policy_label")

    constraints = _optimized_constraint_plot_metrics(constraint_summary)
    constraint_labels = {
        "Biomass supply floor": "Biomass\nsupply",
        "Food-capacity safeguard floor": "Food\ncapacity",
    }
    policy_display_labels = {
        "Conservation Priority": "Conservation",
        "Material Cascade": "Material",
        FOOD_LAND_POLICY_LABEL: "Food",
        "Bioenergy Push": "Bioenergy",
    }
    policy_palette = {
        "Conservation Priority": "#567F5B",
        "Material Cascade": "#B9863B",
        FOOD_LAND_POLICY_LABEL: "#5F86A6",
        "Bioenergy Push": "#A24C42",
    }
    achieved_color = "#5B7C99"
    required_color = "#B63C2F"
    gap_color = "#6F6F6F"

    def format_billions(value_eur: float) -> str:
        return f"€{value_eur / 1_000_000_000:.2f}B"

    fig, (ax_policies, ax_constraints) = plt.subplots(
        1,
        2,
        figsize=(13.6, 6.4),
        gridspec_kw={"width_ratios": [1.2, 1.0]},
        constrained_layout=True,
    )
    fig.set_constrained_layout_pads(w_pad=3 / 72, h_pad=3 / 72, hspace=0.05, wspace=0.08)

    total_value_billion = constraints["portfolio_total_value_eur"].iloc[0] / 1_000_000_000.0
    fig.suptitle(
        f"Optimized portfolio objective value: €{total_value_billion:.2f}B",
        fontsize=15,
        fontweight="semibold",
        y=1.02,
    )

    policy_colors = [policy_palette.get(label, "#777777") for label in summary["optimized_policy_label"]]
    display_labels = [policy_display_labels.get(label, label) for label in summary["optimized_policy_label"]]
    ax_policies.bar(display_labels, summary["region_count"], color=policy_colors)
    ax_policies.set_axisbelow(True)
    ax_policies.yaxis.grid(True, color="#d9dee3", linewidth=0.8, alpha=0.8)
    for _, row in summary.iterrows():
        ax_policies.text(
            policy_display_labels.get(row["optimized_policy_label"], row["optimized_policy_label"]),
            row["region_count"] + 1.5,
            format_billions(float(row["optimized_policy_value_eur"])),
            ha="center",
            va="bottom",
            fontsize=11,
        )
    ax_policies.set_ylim(0, float(summary["region_count"].max()) + 12)
    ax_policies.set_ylabel("Number of NUTS-2 regions", fontsize=14)
    ax_policies.set_title("A. Optimized policy mix", fontsize=16, pad=10)
    ax_policies.tick_params(axis="both", labelsize=12)

    x = list(range(len(constraints)))
    achieved_ratio = constraints["achieved_share_of_requirement"].to_numpy()
    delta_from_requirement = constraints["delta_share_of_requirement"].to_numpy()
    bars = ax_constraints.bar(x, achieved_ratio, color=achieved_color, width=0.55, label="Achieved")
    ax_constraints.axhline(
        1.0,
        color=required_color,
        linewidth=1.8,
        linestyle="--",
        label="Minimum required",
        zorder=2,
    )
    ax_constraints.set_xticks(x, [constraint_labels.get(label, label) for label in constraints["constraint"]])
    ax_constraints.set_ylim(0.0, float(max(1.10, achieved_ratio.max() + 0.12)))
    ax_constraints.set_axisbelow(True)
    ax_constraints.yaxis.grid(True, color="#d9dee3", linewidth=0.8, alpha=0.8)
    ax_constraints.set_ylabel("Achieved relative to requirement (1.0 = target)", fontsize=14)
    ax_constraints.set_title("B. Constraint performance", fontsize=16, pad=10)
    ax_constraints.tick_params(axis="both", labelsize=12)
    ax_constraints.legend(frameon=False, loc="upper left", bbox_to_anchor=(0.01, 0.99), fontsize=12)
    ax_constraints.text(
        0.99,
        1.0,
        "Requirement (target)",
        transform=ax_constraints.get_yaxis_transform(),
        ha="right",
        va="bottom",
        fontsize=10,
        color=required_color,
    )
    ax_constraints.text(
        0.99,
        0.93,
        "Values > 1 exceed requirement",
        transform=ax_constraints.transAxes,
        ha="right",
        va="top",
        fontsize=10,
        color="#4d4d4d",
    )

    for bar, (_, row), ratio, delta in zip(bars, constraints.iterrows(), achieved_ratio, delta_from_requirement, strict=False):
        x_center = bar.get_x() + bar.get_width() / 2.0
        ax_constraints.text(
            x_center,
            ratio + 0.035,
            row["achieved_ratio_label"],
            ha="center",
            va="bottom",
            fontsize=10,
        )
        ax_constraints.text(
            x_center,
            1.0 + delta / 2.0,
            row["delta_ratio_label"],
            ha="center",
            va="center",
            fontsize=10,
            color=gap_color,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.2, "alpha": 0.9},
        )
    _save_figure(output_path)


def plot_sweden_empirical_best_scenario_map(
    best_scenarios: pd.DataFrame,
    nuts2_gdf: gpd.GeoDataFrame,
    output_path: Path,
) -> None:
    plot_df = nuts2_gdf.loc[nuts2_gdf["country_code"] == "SE", ["nuts2_id", "geometry"]].merge(
        best_scenarios[["nuts2_id", "scenario_label", "carbon_value_eur_per_ha"]],
        on="nuts2_id",
        how="left",
    )
    plot_df["plot_color"] = plot_df["scenario_label"].map(SCENARIO_COLORS).fillna("#d9d9d9")

    fig, ax = plt.subplots(figsize=(8.5, 10))
    unique_scenarios = plot_df["scenario_label"].dropna().unique()
    if len(unique_scenarios) == 1:
        plot_df.plot(
            column="carbon_value_eur_per_ha",
            cmap="YlGnBu",
            linewidth=0.6,
            edgecolor="white",
            legend=True,
            ax=ax,
        )
        ax.set_title(
            f"Sweden empirical forest-only best-scenario value per forest hectare\n(all regions select {unique_scenarios[0]})",
            fontsize=14,
            pad=12,
        )
    else:
        plot_df.plot(color=plot_df["plot_color"], edgecolor="white", linewidth=0.6, ax=ax)
        ax.set_title(
            "Sweden NUTS-2 empirical forest-only best scenario\nusing SLU forest area, biomass, and increment data",
            fontsize=14,
            pad=12,
        )
    _set_bounds_with_padding(ax, plot_df)
    _hide_map_axes(ax)

    if len(unique_scenarios) > 1:
        legend_handles = [
            plt.Line2D([0], [0], marker="s", linestyle="", color=SCENARIO_COLORS[label], markersize=10, label=label)
            for label in SCENARIO_ORDER
            if label in unique_scenarios
        ]
        ax.legend(handles=legend_handles, frameon=False, loc="center left", bbox_to_anchor=(1.02, 0.5))
    _save_figure(output_path)


def plot_sweden_empirical_comparison(comparison_df: pd.DataFrame, output_path: Path) -> None:
    plot_df = comparison_df.sort_values("empirical_best_scenario_value_eur_per_ha_land").copy()
    y_positions = range(len(plot_df))

    fig, (ax_values, ax_difference) = plt.subplots(
        1,
        2,
        figsize=(13, 5.8),
        gridspec_kw={"width_ratios": [1.2, 0.9]},
        constrained_layout=True,
    )

    ax_values.barh(
        y_positions,
        plot_df["screening_best_scenario_value_eur_per_ha_land"],
        color="#b8c4d6",
        label="Woodland-share screening",
    )
    ax_values.barh(
        y_positions,
        plot_df["empirical_best_scenario_value_eur_per_ha_land"],
        color="#305f72",
        alpha=0.85,
        label="Empirical Sweden NUTS-2",
    )
    ax_values.set_yticks(list(y_positions), plot_df["nuts2_id"])
    ax_values.set_xlabel("Best-scenario value (EUR/ha of total land)")
    ax_values.set_title("A. Screening versus empirical values")
    handles, legend_labels = ax_values.get_legend_handles_labels()
    fig.legend(handles, legend_labels, frameon=False, loc="outside upper center", ncol=2)

    colors = ["#2f6b3b" if value >= 0 else "#9d1f16" for value in plot_df["best_scenario_benefit_difference_tco2e"]]
    ax_difference.barh(
        y_positions,
        plot_df["best_scenario_benefit_difference_tco2e"] / 1_000_000.0,
        color=colors,
    )
    ax_difference.axvline(0.0, color="#333333", linewidth=0.8)
    ax_difference.set_yticks(list(y_positions), plot_df["nuts2_id"])
    ax_difference.set_xlabel("Empirical minus screening benefit (MtCO2e)")
    ax_difference.set_title("B. How much Sweden changes")
    ax_difference.text(
        0.02,
        0.02,
        "Positive values mean the empirical SLU-based screen is more climate-favorable.",
        transform=ax_difference.transAxes,
        fontsize=8,
    )
    ax_difference.margins(x=0.08)
    _save_figure(output_path)
