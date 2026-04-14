from __future__ import annotations

import json
import logging

import geopandas as gpd
import pandas as pd

from .config import DATA_RAW_DIR, RAW_DATASETS

logger = logging.getLogger(__name__)


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    valid_denominator = denominator.where(denominator > 0.0)
    return numerator / valid_denominator


def load_nuts2_geometries() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(DATA_RAW_DIR / RAW_DATASETS["gisco_nuts2"]["filename"])
    eu_country_codes = {
        "AT",
        "BE",
        "BG",
        "HR",
        "CY",
        "CZ",
        "DK",
        "EE",
        "FI",
        "FR",
        "DE",
        "EL",
        "HU",
        "IE",
        "IT",
        "LV",
        "LT",
        "LU",
        "MT",
        "NL",
        "PL",
        "PT",
        "RO",
        "SK",
        "SI",
        "ES",
        "SE",
    }
    gdf = gdf.loc[gdf["CNTR_CODE"].isin(eu_country_codes), ["NUTS_ID", "CNTR_CODE", "NAME_LATN", "geometry"]].copy()
    gdf = gdf.rename(columns={"NUTS_ID": "nuts2_id", "CNTR_CODE": "country_code", "NAME_LATN": "nuts2_name"})
    return gpd.GeoDataFrame(gdf, geometry="geometry", crs="EPSG:4326")


def _eurostat_json_value(json_obj: dict, *, unit: str, landcover: str, geo: str, time: str) -> float | None:
    ids = json_obj["id"]
    sizes = json_obj["size"]
    indices = {dim: json_obj["dimension"][dim]["category"]["index"] for dim in ids}

    keys = {"freq": "A", "unit": unit, "landcover": landcover, "time": time, "geo": geo}
    storage_order = ["freq", "unit", "landcover", "time", "geo"]

    position = 0
    multiplier = 1
    for dim in reversed(storage_order):
        position += indices[dim][keys[dim]] * multiplier
        multiplier *= sizes[ids.index(dim)]

    raw = json_obj["value"].get(str(position))
    return None if raw is None else float(raw)


def load_nuts2_landcover_context(time: str = "2022") -> pd.DataFrame:
    raw = json.loads((DATA_RAW_DIR / RAW_DATASETS["eurostat_nuts2_landcover"]["filename"]).read_text())
    geos = raw["dimension"]["geo"]["category"]["index"]

    nuts2_codes = sorted(code for code in geos if len(code) == 4 and code[:2].isalpha())
    rows = []
    for nuts2_id in nuts2_codes:
        rows.append(
            {
                "nuts2_id": nuts2_id,
                "total_area_km2": _eurostat_json_value(raw, unit="KM2", landcover="TOTAL", geo=nuts2_id, time=time),
                "woodland_area_km2": _eurostat_json_value(raw, unit="KM2", landcover="C00", geo=nuts2_id, time=time),
                "broadleaved_woodland_km2": _eurostat_json_value(raw, unit="KM2", landcover="C10", geo=nuts2_id, time=time),
                "coniferous_woodland_km2": _eurostat_json_value(raw, unit="KM2", landcover="C20", geo=nuts2_id, time=time),
                "mixed_woodland_km2": _eurostat_json_value(raw, unit="KM2", landcover="C30", geo=nuts2_id, time=time),
                "cropland_area_km2": _eurostat_json_value(raw, unit="KM2", landcover="B00", geo=nuts2_id, time=time),
                "fodder_crops_km2": _eurostat_json_value(raw, unit="KM2", landcover="B50", geo=nuts2_id, time=time),
                "temporary_grassland_km2": _eurostat_json_value(raw, unit="KM2", landcover="B55", geo=nuts2_id, time=time),
                "fruit_and_berry_area_km2": _eurostat_json_value(raw, unit="KM2", landcover="B70", geo=nuts2_id, time=time),
                "other_permanent_crop_area_km2": _eurostat_json_value(raw, unit="KM2", landcover="B80", geo=nuts2_id, time=time),
                "grassland_area_km2": _eurostat_json_value(raw, unit="KM2", landcover="E00", geo=nuts2_id, time=time),
            }
        )

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["total_area_km2", "woodland_area_km2"]).copy()
    woodland_detail_columns = [
        "broadleaved_woodland_km2",
        "coniferous_woodland_km2",
        "mixed_woodland_km2",
    ]
    agricultural_detail_columns = [
        "cropland_area_km2",
        "fodder_crops_km2",
        "temporary_grassland_km2",
        "fruit_and_berry_area_km2",
        "other_permanent_crop_area_km2",
        "grassland_area_km2",
    ]
    df["has_missing_woodland_composition_detail"] = df[woodland_detail_columns].isna().any(axis=1)
    df["has_missing_agricultural_detail"] = df[agricultural_detail_columns].isna().any(axis=1)
    area_columns = [
        *woodland_detail_columns,
        *agricultural_detail_columns,
    ]
    woodland_missing_count = int(df["has_missing_woodland_composition_detail"].sum())
    agricultural_missing_count = int(df["has_missing_agricultural_detail"].sum())
    if woodland_missing_count:
        logger.warning(
            "Found %s NUTS-2 rows with missing woodland subclass detail; those values are zero-filled downstream.",
            woodland_missing_count,
        )
    if agricultural_missing_count:
        logger.warning(
            "Found %s NUTS-2 rows with missing agricultural detail; those values are zero-filled downstream.",
            agricultural_missing_count,
        )
    df[area_columns] = df[area_columns].fillna(0.0)
    df["woodland_share_of_land"] = _safe_divide(df["woodland_area_km2"], df["total_area_km2"])
    df["broadleaved_share_of_woodland"] = _safe_divide(df["broadleaved_woodland_km2"], df["woodland_area_km2"])
    df["coniferous_share_of_woodland"] = _safe_divide(df["coniferous_woodland_km2"], df["woodland_area_km2"])
    df["mixed_share_of_woodland"] = _safe_divide(df["mixed_woodland_km2"], df["woodland_area_km2"])
    df["permanent_crop_area_km2"] = df["fruit_and_berry_area_km2"] + df["other_permanent_crop_area_km2"]
    df["agricultural_land_area_km2"] = df["cropland_area_km2"] + df["grassland_area_km2"]
    df["feed_land_area_km2"] = df["fodder_crops_km2"] + df["temporary_grassland_km2"] + df["grassland_area_km2"]
    df["cropland_share_of_land"] = _safe_divide(df["cropland_area_km2"], df["total_area_km2"])
    df["grassland_share_of_land"] = _safe_divide(df["grassland_area_km2"], df["total_area_km2"])
    df["agricultural_land_share_of_land"] = _safe_divide(df["agricultural_land_area_km2"], df["total_area_km2"])
    ag_nonzero = df["agricultural_land_area_km2"].where(df["agricultural_land_area_km2"] > 0.0)
    df["feed_land_share_of_agricultural_land"] = (df["feed_land_area_km2"] / ag_nonzero).fillna(0.0).clip(upper=1.0)
    df["permanent_crop_share_of_agricultural_land"] = (
        df["permanent_crop_area_km2"] / ag_nonzero
    ).fillna(0.0).clip(upper=1.0)
    return df


def _apply_empirical_screening_override(
    nuts2: pd.DataFrame,
    empirical_baseline: pd.DataFrame,
    empirical_best: pd.DataFrame,
) -> pd.DataFrame:
    empirical = empirical_baseline[
        [
            "nuts2_id",
            "nuts2_name",
            "forest_area_ha",
            "forest_carbon_stock_mtco2e",
            "harvest_total_m3",
            "carbon_stock_density_tco2e_per_ha",
            "harvest_intensity_m3_per_ha",
            "biodiversity_pressure_proxy",
        ]
    ].merge(
        empirical_best[
            [
                "nuts2_id",
                "scenario",
                "scenario_label",
                "net_climate_benefit_tco2e",
                "carbon_value_eur",
                "net_climate_benefit_tco2e_per_ha",
                "carbon_value_eur_per_ha",
            ]
        ],
        on="nuts2_id",
        how="inner",
    )
    empirical["estimated_forest_area_ha"] = empirical["forest_area_ha"]
    empirical["estimated_forest_carbon_stock_mtco2e"] = empirical["forest_carbon_stock_mtco2e"]
    empirical["estimated_best_scenario_benefit_tco2e"] = empirical["net_climate_benefit_tco2e"]
    empirical["estimated_best_scenario_carbon_value_eur"] = empirical["carbon_value_eur"]
    empirical["forest_data_source"] = "SLU NFI county aggregation"

    override_columns = [
        "nuts2_id",
        "nuts2_name",
        "forest_area_ha",
        "forest_carbon_stock_mtco2e",
        "harvest_total_m3",
        "carbon_stock_density_tco2e_per_ha",
        "harvest_intensity_m3_per_ha",
        "biodiversity_pressure_proxy",
        "scenario",
        "scenario_label",
        "net_climate_benefit_tco2e",
        "carbon_value_eur",
        "net_climate_benefit_tco2e_per_ha",
        "carbon_value_eur_per_ha",
        "estimated_forest_area_ha",
        "estimated_forest_carbon_stock_mtco2e",
        "estimated_best_scenario_benefit_tco2e",
        "estimated_best_scenario_carbon_value_eur",
        "forest_data_source",
    ]
    override = empirical[override_columns].rename(
        columns={
            "scenario": "scenario_empirical",
            "scenario_label": "scenario_label_empirical",
            "net_climate_benefit_tco2e": "net_climate_benefit_tco2e_empirical",
            "carbon_value_eur": "carbon_value_eur_empirical",
            "net_climate_benefit_tco2e_per_ha": "net_climate_benefit_tco2e_per_ha_empirical",
            "carbon_value_eur_per_ha": "carbon_value_eur_per_ha_empirical",
            "forest_area_ha": "forest_area_ha_empirical",
            "forest_carbon_stock_mtco2e": "forest_carbon_stock_mtco2e_empirical",
            "harvest_total_m3": "harvest_total_m3_empirical",
            "carbon_stock_density_tco2e_per_ha": "carbon_stock_density_tco2e_per_ha_empirical",
            "harvest_intensity_m3_per_ha": "harvest_intensity_m3_per_ha_empirical",
            "biodiversity_pressure_proxy": "biodiversity_pressure_proxy_empirical",
            "estimated_forest_area_ha": "estimated_forest_area_ha_empirical",
            "estimated_forest_carbon_stock_mtco2e": "estimated_forest_carbon_stock_mtco2e_empirical",
            "estimated_best_scenario_benefit_tco2e": "estimated_best_scenario_benefit_tco2e_empirical",
            "estimated_best_scenario_carbon_value_eur": "estimated_best_scenario_carbon_value_eur_empirical",
            "forest_data_source": "forest_data_source_empirical",
            "nuts2_name": "nuts2_name_empirical",
        }
    )

    merged = nuts2.merge(override, on="nuts2_id", how="left")
    for column in [
        "nuts2_name",
        "forest_area_ha",
        "forest_carbon_stock_mtco2e",
        "harvest_total_m3",
        "carbon_stock_density_tco2e_per_ha",
        "harvest_intensity_m3_per_ha",
        "biodiversity_pressure_proxy",
        "scenario",
        "scenario_label",
        "net_climate_benefit_tco2e",
        "carbon_value_eur",
        "net_climate_benefit_tco2e_per_ha",
        "carbon_value_eur_per_ha",
        "estimated_forest_area_ha",
        "estimated_forest_carbon_stock_mtco2e",
        "estimated_best_scenario_benefit_tco2e",
        "estimated_best_scenario_carbon_value_eur",
        "forest_data_source",
    ]:
        empirical_column = f"{column}_empirical"
        if empirical_column in merged.columns:
            merged[column] = merged[empirical_column].combine_first(merged[column])

    drop_columns = [column for column in merged.columns if column.endswith("_empirical")]
    return merged.drop(columns=drop_columns)


def compare_sweden_empirical_to_screening(
    screening_gdf: pd.DataFrame,
    empirical_baseline: pd.DataFrame,
    empirical_best: pd.DataFrame,
) -> pd.DataFrame:
    share_based = screening_gdf.loc[screening_gdf["country_code"] == "SE"].copy()
    comparison = share_based[
        [
            "nuts2_id",
            "nuts2_name",
            "total_area_km2",
            "estimated_forest_area_ha",
            "estimated_forest_carbon_stock_mtco2e",
            "estimated_best_scenario_benefit_tco2e",
            "estimated_best_scenario_value_eur_per_ha_land",
            "screening_priority_score",
        ]
    ].rename(
        columns={
            "estimated_forest_area_ha": "screening_forest_area_ha",
            "estimated_forest_carbon_stock_mtco2e": "screening_forest_carbon_stock_mtco2e",
            "estimated_best_scenario_benefit_tco2e": "screening_best_scenario_benefit_tco2e",
            "estimated_best_scenario_value_eur_per_ha_land": "screening_best_scenario_value_eur_per_ha_land",
            "screening_priority_score": "screening_priority_score_share_based",
        }
    )
    empirical = empirical_baseline[
        [
            "nuts2_id",
            "nuts2_name",
            "forest_area_ha",
            "forest_carbon_stock_mtco2e",
        ]
    ].merge(
        empirical_best[
            [
                "nuts2_id",
                "scenario_label",
                "net_climate_benefit_tco2e",
                "carbon_value_eur",
            ]
        ],
        on="nuts2_id",
        how="left",
    )
    empirical = empirical.rename(
        columns={
            "forest_area_ha": "empirical_forest_area_ha",
            "forest_carbon_stock_mtco2e": "empirical_forest_carbon_stock_mtco2e",
            "scenario_label": "empirical_best_scenario_label",
            "net_climate_benefit_tco2e": "empirical_best_scenario_benefit_tco2e",
            "carbon_value_eur": "empirical_best_scenario_value_eur",
        }
    )
    comparison = comparison.merge(empirical, on=["nuts2_id", "nuts2_name"], how="left")
    comparison["forest_area_difference_ha"] = comparison["empirical_forest_area_ha"] - comparison["screening_forest_area_ha"]
    comparison["forest_carbon_difference_mtco2e"] = (
        comparison["empirical_forest_carbon_stock_mtco2e"] - comparison["screening_forest_carbon_stock_mtco2e"]
    )
    comparison["best_scenario_benefit_difference_tco2e"] = (
        comparison["empirical_best_scenario_benefit_tco2e"] - comparison["screening_best_scenario_benefit_tco2e"]
    )
    comparison["empirical_best_scenario_value_eur_per_ha_land"] = (
        comparison["empirical_best_scenario_value_eur"] / (comparison["total_area_km2"] * 100.0)
    )
    return comparison.sort_values("nuts2_id").reset_index(drop=True)


def build_nuts2_screening_dataset(
    baseline_metrics: pd.DataFrame,
    best_scenarios: pd.DataFrame,
    country_modal_scenario: pd.DataFrame,
    sweden_empirical_case: dict[str, pd.DataFrame] | None = None,
) -> gpd.GeoDataFrame:
    geometries = load_nuts2_geometries()
    landcover = load_nuts2_landcover_context()
    geometry_ids = set(geometries["nuts2_id"])
    landcover_ids = set(landcover["nuts2_id"])
    dropped_geometry_ids = sorted(geometry_ids - landcover_ids)
    if dropped_geometry_ids:
        logger.warning(
            "Dropping %s NUTS-2 regions from the screening dataset because the selected Eurostat land-cover layer has no exact nuts2_id match.",
            len(dropped_geometry_ids),
        )

    baseline_columns = [
        "country",
        "country_code",
        "forest_area_ha",
        "forest_carbon_stock_mtco2e",
        "harvest_total_m3",
        "carbon_stock_density_tco2e_per_ha",
        "harvest_intensity_m3_per_ha",
        "biodiversity_pressure_proxy",
    ]
    optional_baseline_columns = [
        "selected_food_crop_area_kha",
        "selected_food_production_kt",
        "food_production_intensity_index",
    ]
    baseline_lookup = baseline_metrics[
        baseline_columns + [column for column in optional_baseline_columns if column in baseline_metrics.columns]
    ].copy()
    best_lookup = best_scenarios[
        [
            "country",
            "country_code",
            "scenario",
            "scenario_label",
            "net_climate_benefit_tco2e",
            "carbon_value_eur",
            "net_climate_benefit_tco2e_per_ha",
            "carbon_value_eur_per_ha",
        ]
    ].copy()
    modal_lookup = country_modal_scenario[
        [
            "country",
            "country_code",
            "scenario",
            "scenario_label",
            "share_best",
            "runner_up_scenario_label",
            "robustness_margin",
        ]
    ].copy().rename(
        columns={
            "scenario": "modal_scenario",
            "scenario_label": "modal_scenario_label",
            "share_best": "modal_scenario_share_best",
        }
    )

    nuts2 = geometries.merge(landcover, on="nuts2_id", how="inner")
    nuts2["landcover_join_status"] = "matched"
    nuts2["landcover_regions_dropped_count"] = len(dropped_geometry_ids)
    nuts2 = nuts2.merge(baseline_lookup, on="country_code", how="left")
    nuts2 = nuts2.merge(best_lookup, on=["country_code", "country"], how="left")
    nuts2 = nuts2.merge(modal_lookup, on=["country_code", "country"], how="left")

    country_woodland = nuts2.groupby("country_code", as_index=False)["woodland_area_km2"].sum().rename(
        columns={"woodland_area_km2": "country_woodland_area_km2"}
    )
    nuts2 = nuts2.merge(country_woodland, on="country_code", how="left")
    nuts2["share_of_country_woodland"] = nuts2["woodland_area_km2"] / nuts2["country_woodland_area_km2"]

    nuts2["estimated_forest_area_ha"] = nuts2["forest_area_ha"] * nuts2["share_of_country_woodland"]
    nuts2["estimated_forest_carbon_stock_mtco2e"] = nuts2["forest_carbon_stock_mtco2e"] * nuts2["share_of_country_woodland"]
    nuts2["estimated_best_scenario_benefit_tco2e"] = nuts2["net_climate_benefit_tco2e"] * nuts2["share_of_country_woodland"]
    nuts2["estimated_best_scenario_carbon_value_eur"] = nuts2["carbon_value_eur"] * nuts2["share_of_country_woodland"]
    nuts2["estimated_best_scenario_benefit_tco2e_per_km2_land"] = (
        nuts2["estimated_best_scenario_benefit_tco2e"] / nuts2["total_area_km2"]
    )
    nuts2["estimated_best_scenario_value_eur_per_ha_land"] = (
        nuts2["estimated_best_scenario_carbon_value_eur"] / (nuts2["total_area_km2"] * 100.0)
    )
    nuts2["forest_data_source"] = "Country totals downscaled by NUTS-2 woodland share"

    if sweden_empirical_case is not None:
        nuts2 = _apply_empirical_screening_override(
            nuts2,
            empirical_baseline=sweden_empirical_case["baseline_metrics"],
            empirical_best=sweden_empirical_case["best_scenarios"],
        )

    nuts2["estimated_best_scenario_benefit_tco2e_per_km2_land"] = (
        nuts2["estimated_best_scenario_benefit_tco2e"] / nuts2["total_area_km2"]
    )
    nuts2["estimated_best_scenario_value_eur_per_ha_land"] = (
        nuts2["estimated_best_scenario_carbon_value_eur"] / (nuts2["total_area_km2"] * 100.0)
    )
    nuts2["screening_priority_score"] = (
        (nuts2["estimated_best_scenario_carbon_value_eur"] / 1_000_000.0)
        * nuts2["woodland_share_of_land"]
        * nuts2["modal_scenario_share_best"]
    )
    nuts2["value_eur_per_land_ha"] = nuts2["estimated_best_scenario_value_eur_per_ha_land"]
    nuts2["benefit_tco2e_per_land_km2"] = nuts2["estimated_best_scenario_benefit_tco2e_per_km2_land"]
    nuts2["is_forest_only"] = True
    nuts2["includes_food_policy"] = False
    nuts2["available_policy_options"] = "conservation_priority|material_cascade|bioenergy_push"
    nuts2["excluded_policy_categories"] = "food_land_safeguard"

    return gpd.GeoDataFrame(nuts2, geometry="geometry", crs="EPSG:4326")


def top_nuts2_regions(screening_gdf: gpd.GeoDataFrame, n: int = 25) -> pd.DataFrame:
    top = screening_gdf.sort_values("screening_priority_score", ascending=False).head(n).copy()
    return top[
        [
            "nuts2_id",
            "nuts2_name",
            "country",
            "modal_scenario_label",
            "modal_scenario_share_best",
            "woodland_share_of_land",
            "coniferous_share_of_woodland",
            "broadleaved_share_of_woodland",
            "estimated_best_scenario_benefit_tco2e",
            "estimated_best_scenario_value_eur_per_ha_land",
            "screening_priority_score",
        ]
    ]
