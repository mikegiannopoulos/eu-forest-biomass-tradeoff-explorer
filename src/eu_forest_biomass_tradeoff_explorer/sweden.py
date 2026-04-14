from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

import geopandas as gpd
import pandas as pd

from .config import (
    DATA_RAW_DIR,
    DEFAULT_MODEL_PARAMETERS,
    RAW_DATASETS,
    SWEDEN_BIOMASS_CARBON_FRACTION,
    SWEDEN_COUNTY_TO_NUTS2,
    SWEDEN_SLU_API_BASE_URL,
    SWEDEN_SLU_TABLES,
    ModelParameters,
)
from .model import best_scenario_by_country, build_baseline_metrics, evaluate_scenarios


def _raw_path(dataset_key: str) -> Path:
    return DATA_RAW_DIR / RAW_DATASETS[dataset_key]["filename"]


def _request_json(url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method="POST" if payload is not None else "GET")
    with urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _table_url(table_key: str) -> str:
    return f"{SWEDEN_SLU_API_BASE_URL}/{SWEDEN_SLU_TABLES[table_key]['path']}"


def _variable(metadata: dict, variable_text: str) -> dict:
    for variable in metadata["variables"]:
        if variable["text"] == variable_text:
            return variable
    raise KeyError(f"Variable text not found in SLU metadata: {variable_text}")


def _value_code(variable: dict, value_text: str) -> str:
    for code, text in zip(variable["values"], variable["valueTexts"], strict=True):
        if text == value_text:
            return code
    raise KeyError(f"Value text not found in SLU metadata: {value_text}")


def _county_selections(metadata: dict) -> tuple[list[str], dict[str, str]]:
    county_variable = _variable(metadata, "County")
    county_codes: list[str] = []
    county_lookup: dict[str, str] = {}
    for code, text in zip(county_variable["values"], county_variable["valueTexts"], strict=True):
        if text.endswith("län"):
            county_codes.append(code)
            county_lookup[code] = text
    return county_codes, county_lookup


def _build_query(table_key: str, metadata: dict) -> dict:
    table = SWEDEN_SLU_TABLES[table_key]
    county_codes, _ = _county_selections(metadata)
    year_variable = _variable(metadata, table["year_variable_text"])

    query = [
        {
            "code": year_variable["code"],
            "selection": {
                "filter": "item",
                "values": [_value_code(year_variable, table["year_value_text"])],
            },
        },
        {
            "code": _variable(metadata, "County")["code"],
            "selection": {
                "filter": "item",
                "values": county_codes,
            },
        },
    ]

    for variable_text, value_text in table["fixed_selections"].items():
        variable = _variable(metadata, variable_text)
        query.append(
            {
                "code": variable["code"],
                "selection": {
                    "filter": "item",
                    "values": [_value_code(variable, value_text)],
                },
            }
        )

    return {
        "query": query,
        "response": {
            "format": "json",
        },
    }


def download_sweden_slu_raw_data(force: bool = False) -> None:
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    for table_key, table in SWEDEN_SLU_TABLES.items():
        metadata_path = _raw_path(table["metadata_dataset"])
        data_path = _raw_path(table["data_dataset"])

        if force or not metadata_path.exists():
            metadata = _request_json(_table_url(table_key))
            _write_json(metadata_path, metadata)
        else:
            metadata = _read_json(metadata_path)

        if force or not data_path.exists():
            query = _build_query(table_key, metadata)
            response = _request_json(_table_url(table_key), payload=query)
            _write_json(data_path, response)


def _parse_table_response(table_key: str, metadata: dict, response: dict) -> pd.DataFrame:
    table = SWEDEN_SLU_TABLES[table_key]
    county_lookup = _county_selections(metadata)[1]

    data_columns = [column for column in response["columns"] if column["type"] != "c"]
    county_position = next(index for index, column in enumerate(data_columns) if column["text"] == "County")

    rows: list[dict[str, float | str]] = []
    for record in response["data"]:
        county_code = record["key"][county_position]
        raw_value = record["values"][0]
        rows.append(
            {
                "county_name": county_lookup[county_code],
                table["value_column"]: float(raw_value) if raw_value not in {"..", ":"} else float("nan"),
            }
        )

    return pd.DataFrame(rows)


def load_sweden_county_empirical_metrics() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for table_key, table in SWEDEN_SLU_TABLES.items():
        metadata = _read_json(_raw_path(table["metadata_dataset"]))
        response = _read_json(_raw_path(table["data_dataset"]))
        frames.append(_parse_table_response(table_key, metadata, response))

    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="county_name", how="inner")

    merged["nuts2_id"] = merged["county_name"].map(SWEDEN_COUNTY_TO_NUTS2)
    if merged["nuts2_id"].isna().any():
        missing = ", ".join(sorted(merged.loc[merged["nuts2_id"].isna(), "county_name"].unique()))
        raise ValueError(f"Missing Swedish county-to-NUTS2 mapping for: {missing}")

    return merged.sort_values("county_name").reset_index(drop=True)


def _load_sweden_nuts2_lookup() -> pd.DataFrame:
    gdf = gpd.read_file(DATA_RAW_DIR / RAW_DATASETS["gisco_nuts2"]["filename"])
    sweden = gdf.loc[gdf["CNTR_CODE"] == "SE", ["NUTS_ID", "NAME_LATN"]].copy()
    sweden = sweden.rename(columns={"NUTS_ID": "nuts2_id", "NAME_LATN": "nuts2_name"})
    return pd.DataFrame(sweden.drop_duplicates(subset=["nuts2_id"]))


def build_sweden_empirical_nuts2_case_study(
    baseline_inputs: pd.DataFrame,
    reference_metrics: pd.DataFrame,
    parameters: ModelParameters = DEFAULT_MODEL_PARAMETERS,
) -> dict[str, pd.DataFrame]:
    county_metrics = load_sweden_county_empirical_metrics()
    nuts2_lookup = _load_sweden_nuts2_lookup()

    nuts2_metrics = (
        county_metrics.groupby("nuts2_id", as_index=False)[
            [
                "productive_forest_area_kha",
                "annual_increment_10000_m3sk",
                "total_biomass_million_t_dry",
            ]
        ]
        .sum()
        .merge(nuts2_lookup, on="nuts2_id", how="left")
    )

    sweden_row = baseline_inputs.loc[baseline_inputs["country_code"] == "SE"].squeeze()
    if sweden_row.empty:
        raise ValueError("Sweden was not found in the country-level baseline inputs.")

    national_increment_10000_m3sk = nuts2_metrics["annual_increment_10000_m3sk"].sum()
    if national_increment_10000_m3sk <= 0.0:
        raise ValueError("Sweden empirical increment totals are zero; cannot build harvest allocation shares.")

    nuts2_metrics["forest_area_share_of_sweden"] = (
        nuts2_metrics["productive_forest_area_kha"] / nuts2_metrics["productive_forest_area_kha"].sum()
    )
    nuts2_metrics["increment_share_of_sweden"] = (
        nuts2_metrics["annual_increment_10000_m3sk"] / national_increment_10000_m3sk
    )
    nuts2_metrics["forest_carbon_stock_mt_c"] = (
        nuts2_metrics["total_biomass_million_t_dry"] * SWEDEN_BIOMASS_CARBON_FRACTION
    )

    harvest_share = nuts2_metrics["increment_share_of_sweden"]
    forest_area = nuts2_metrics["productive_forest_area_kha"]

    regional_inputs = pd.DataFrame(
        {
            "country": nuts2_metrics["nuts2_name"],
            "country_code": "SE",
            "iso3_code": "SWE",
            "parent_country": "Sweden",
            "nuts2_id": nuts2_metrics["nuts2_id"],
            "nuts2_name": nuts2_metrics["nuts2_name"],
            "source_layer": "sweden_slu_empirical",
            "forest_area_kha": forest_area,
            "forest_carbon_stock_mt_c": nuts2_metrics["forest_carbon_stock_mt_c"],
            "naturally_regenerating_forest_kha": forest_area * (sweden_row["naturally_regenerating_forest_kha"] / sweden_row["forest_area_kha"]),
            "planted_forest_kha": forest_area * (sweden_row["planted_forest_kha"] / sweden_row["forest_area_kha"]),
            "primary_forest_kha": forest_area * (sweden_row["primary_forest_kha"] / sweden_row["forest_area_kha"]),
            "roundwood_m3": sweden_row["roundwood_m3"] * harvest_share,
            "industrial_roundwood_m3": sweden_row["industrial_roundwood_m3"] * harvest_share,
            "wood_fuel_m3": sweden_row["wood_fuel_m3"] * harvest_share,
            "sawnwood_m3": sweden_row["sawnwood_m3"] * harvest_share,
            "wood_pellets_t": sweden_row["wood_pellets_t"] * harvest_share,
            "selected_food_crop_area_kha": 0.0,
            "selected_food_production_kt": 0.0,
            "food_production_intensity_index": 0.0,
        }
    )

    empirical_baseline = build_baseline_metrics(
        regional_inputs,
        parameters=parameters,
        reference_metrics=reference_metrics,
    )
    empirical_scenarios = evaluate_scenarios(empirical_baseline, parameters=parameters)
    empirical_best = best_scenario_by_country(empirical_scenarios)

    return {
        "county_metrics": county_metrics,
        "nuts2_metrics": nuts2_metrics,
        "regional_inputs": regional_inputs,
        "baseline_metrics": empirical_baseline,
        "scenario_results": empirical_scenarios,
        "best_scenarios": empirical_best,
    }
