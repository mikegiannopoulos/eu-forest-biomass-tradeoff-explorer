from __future__ import annotations

import json
import urllib.request
import zipfile

import geopandas as gpd
import pandas as pd

from .config import (
    ANALYSIS_YEAR,
    DATA_PROCESSED_DIR,
    DATA_RAW_DIR,
    EU_COUNTRIES,
    FORESTRY_VARIABLES,
    LAND_USE_VARIABLES,
    RAW_DATASETS,
)
from .sweden import download_sweden_slu_raw_data


CROP_CODES = {
    "C0000": "cereals",
    "P0000": "pulses",
    "R1000": "potatoes",
    "V0000": "vegetables",
}

STRUCTURE_CODES = {
    "AR": "area_kha",
    "PR_HU_EU": "production_kt",
    "YI_HU_EU": "yield_t_per_ha",
}


def ensure_directories() -> None:
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def download_raw_data(force: bool = False) -> None:
    ensure_directories()
    for dataset in RAW_DATASETS.values():
        if "url" not in dataset:
            continue
        target = DATA_RAW_DIR / dataset["filename"]
        if target.exists() and not force:
            continue
        urllib.request.urlretrieve(dataset["url"], target)
    download_sweden_slu_raw_data(force=force)


def _country_lookup_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "country": [country.country for country in EU_COUNTRIES],
            "country_code": [country.country_code for country in EU_COUNTRIES],
            "iso3_code": [country.iso3_code for country in EU_COUNTRIES],
            "faostat_area": [country.faostat_area for country in EU_COUNTRIES],
        }
    )


def _read_filtered_faostat(
    zip_path,
    *,
    usecols: list[str],
    filters: dict[str, list[str] | list[int]],
    chunksize: int = 250_000,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(zip_path) as archive:
        try:
            csv_name = next(name for name in archive.namelist() if name.endswith("_All_Data_(Normalized).csv"))
        except StopIteration as exc:
            raise FileNotFoundError(f"No normalized data CSV found in {zip_path}") from exc

        with archive.open(csv_name) as buffer:
            for chunk in pd.read_csv(buffer, usecols=usecols, chunksize=chunksize):
                mask = pd.Series(True, index=chunk.index)
                for column, values in filters.items():
                    mask &= chunk[column].isin(values)
                filtered = chunk.loc[mask].copy()
                if not filtered.empty:
                    frames.append(filtered)

    if not frames:
        return pd.DataFrame(columns=usecols)
    return pd.concat(frames, ignore_index=True)


def _jsonstat_value(json_obj: dict, selectors: dict[str, str]) -> float | None:
    ids = json_obj["id"]
    sizes = json_obj["size"]
    indices = {dim: json_obj["dimension"][dim]["category"]["index"] for dim in ids}

    position = 0
    multiplier = 1
    for dim in reversed(ids):
        position += indices[dim][selectors[dim]] * multiplier
        multiplier *= sizes[ids.index(dim)]

    raw = json_obj["value"].get(str(position))
    return None if raw is None else float(raw)


def load_land_use_inputs(year: int = ANALYSIS_YEAR) -> pd.DataFrame:
    lookup = _country_lookup_frame()
    variables = pd.DataFrame(LAND_USE_VARIABLES, columns=["Item", "Element", "variable"])
    land_use = _read_filtered_faostat(
        DATA_RAW_DIR / RAW_DATASETS["land_use"]["filename"],
        usecols=["Area", "Item", "Element", "Year", "Value"],
        filters={
            "Area": lookup["faostat_area"].tolist(),
            "Item": variables["Item"].drop_duplicates().tolist(),
            "Element": variables["Element"].drop_duplicates().tolist(),
            "Year": [year],
        },
    )
    land_use = land_use.merge(variables, on=["Item", "Element"], how="inner")
    land_use = land_use.merge(lookup, left_on="Area", right_on="faostat_area", how="inner")
    wide = land_use.pivot_table(index=["country", "country_code", "iso3_code"], columns="variable", values="Value")
    return wide.reset_index()


def load_forestry_inputs(year: int = ANALYSIS_YEAR) -> pd.DataFrame:
    lookup = _country_lookup_frame()
    variables = pd.DataFrame(FORESTRY_VARIABLES, columns=["Item", "Element", "variable"])
    forestry = _read_filtered_faostat(
        DATA_RAW_DIR / RAW_DATASETS["forestry"]["filename"],
        usecols=["Area", "Item", "Element", "Year", "Value"],
        filters={
            "Area": lookup["faostat_area"].tolist(),
            "Item": variables["Item"].drop_duplicates().tolist(),
            "Element": variables["Element"].drop_duplicates().tolist(),
            "Year": [year],
        },
    )
    forestry = forestry.merge(variables, on=["Item", "Element"], how="inner")
    forestry = forestry.merge(lookup, left_on="Area", right_on="faostat_area", how="inner")
    wide = forestry.pivot_table(index=["country", "country_code", "iso3_code"], columns="variable", values="Value")
    return wide.reset_index()


def load_crop_production_profile(year: int = ANALYSIS_YEAR) -> pd.DataFrame:
    raw = json.loads((DATA_RAW_DIR / RAW_DATASETS["eurostat_crop_production"]["filename"]).read_text())

    rows: list[dict[str, float | str]] = []
    for country in EU_COUNTRIES:
        row: dict[str, float | str] = {
            "country": country.country,
            "country_code": country.country_code,
            "iso3_code": country.iso3_code,
        }
        for crop_code, crop_name in CROP_CODES.items():
            for structure_code, structure_name in STRUCTURE_CODES.items():
                row[f"{crop_name}_{structure_name}"] = _jsonstat_value(
                    raw,
                    {
                        "freq": "A",
                        "crops": crop_code,
                        "strucpro": structure_code,
                        "geo": country.country_code,
                        "time": str(year),
                    },
                )
        rows.append(row)

    df = pd.DataFrame(rows)
    crop_names = list(CROP_CODES.values())
    area_columns = [f"{crop_name}_area_kha" for crop_name in crop_names]
    production_columns = [f"{crop_name}_production_kt" for crop_name in crop_names]
    yield_columns = [f"{crop_name}_yield_t_per_ha" for crop_name in crop_names]
    df[area_columns + production_columns + yield_columns] = df[area_columns + production_columns + yield_columns].fillna(0.0)

    selected_crop_area = df[area_columns].sum(axis=1).replace(0.0, pd.NA)
    df["selected_food_crop_area_kha"] = selected_crop_area.fillna(0.0)
    df["selected_food_production_kt"] = df[production_columns].sum(axis=1)

    yield_ratio_columns: list[str] = []
    weighted_yield_ratio = pd.Series(0.0, index=df.index)
    for crop_name in crop_names:
        yield_column = f"{crop_name}_yield_t_per_ha"
        area_column = f"{crop_name}_area_kha"
        median_yield = df.loc[df[yield_column] > 0.0, yield_column].median()
        ratio_column = f"{crop_name}_yield_ratio_to_eu_median"
        if pd.isna(median_yield) or median_yield == 0.0:
            df[ratio_column] = 1.0
        else:
            df[ratio_column] = (df[yield_column] / median_yield).replace([pd.NA], 0.0).fillna(0.0)
        yield_ratio_columns.append(ratio_column)
        area_share = (df[area_column] / selected_crop_area).fillna(0.0)
        weighted_yield_ratio = weighted_yield_ratio + area_share * df[ratio_column]

    df["food_production_intensity_index"] = weighted_yield_ratio.where(selected_crop_area.notna(), 0.0)
    intensity_nonzero = df["food_production_intensity_index"].where(df["food_production_intensity_index"] > 0.0)
    median_intensity = intensity_nonzero.median()
    if pd.notna(median_intensity) and median_intensity > 0.0:
        df["food_production_intensity_index"] = (
            df["food_production_intensity_index"] / median_intensity
        ).where(selected_crop_area.notna(), 0.0)

    return df[["country", "country_code", "iso3_code", "selected_food_crop_area_kha", "selected_food_production_kt", "food_production_intensity_index"]]


def load_country_geometries() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(DATA_RAW_DIR / RAW_DATASETS["gisco_countries"]["filename"])
    gdf = gdf.loc[gdf["EU_STAT"] == "T", ["CNTR_ID", "ISO3_CODE", "geometry"]].copy()
    gdf = gdf.rename(columns={"CNTR_ID": "country_code", "ISO3_CODE": "iso3_code"})
    lookup = _country_lookup_frame()[["country", "country_code", "iso3_code"]]
    gdf = gdf.merge(lookup, on=["country_code", "iso3_code"], how="inner")
    return gpd.GeoDataFrame(gdf, geometry="geometry", crs="EPSG:4326")


def build_baseline_inputs(year: int = ANALYSIS_YEAR) -> pd.DataFrame:
    land_use = load_land_use_inputs(year=year)
    forestry = load_forestry_inputs(year=year)
    crop_profile = load_crop_production_profile(year=year)
    baseline = land_use.merge(forestry, on=["country", "country_code", "iso3_code"], how="inner")
    baseline = baseline.merge(crop_profile, on=["country", "country_code", "iso3_code"], how="left")

    required_columns = [
        "forest_area_kha",
        "forest_carbon_stock_mt_c",
        "naturally_regenerating_forest_kha",
        "planted_forest_kha",
        "roundwood_m3",
        "industrial_roundwood_m3",
        "wood_fuel_m3",
        "sawnwood_m3",
    ]
    missing = baseline[required_columns].isna().any()
    if missing.any():
        missing_columns = ", ".join(missing.index[missing].tolist())
        raise ValueError(f"Missing required FAOSTAT inputs for columns: {missing_columns}")

    baseline = baseline.sort_values("country").reset_index(drop=True)
    return baseline
