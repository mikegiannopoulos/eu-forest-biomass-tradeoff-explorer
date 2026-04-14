# Data Provenance

## Purpose

This note centralizes the raw-data provenance that was previously split across `config.py`, README text, and embedded source metadata.

## Source inventory

| Local file | Source system | How it is obtained | Used by |
| --- | --- | --- | --- |
| `data/raw/Inputs_LandUse_E_All_Data_(Normalized).zip` | FAOSTAT bulk land-use download | URL in `config.py` | `data.py::load_land_use_inputs()` |
| `data/raw/Forestry_E_All_Data_(Normalized).zip` | FAOSTAT bulk forestry download | URL in `config.py` | `data.py::load_forestry_inputs()` |
| `data/raw/CNTR_RG_20M_2024_4326.geojson` | Eurostat GISCO countries | URL in `config.py` | `data.py::load_country_geometries()` |
| `data/raw/NUTS_RG_20M_2024_4326_LEVL_2.geojson` | Eurostat GISCO NUTS-2 | URL in `config.py` | `regional.py::load_nuts2_geometries()` |
| `data/raw/lan_lcv_ovw.json` | Eurostat `lan_lcv_ovw` JSON-stat | URL in `config.py` | `regional.py::load_nuts2_landcover_context()` |
| `data/raw/apro_cpsh1_selected_2024.json` | Eurostat `apro_cpsh1` JSON-stat | URL in `config.py` | `data.py::load_crop_production_profile()` |
| `data/raw/sweden_slu_area_metadata.json` | SLU PxWeb metadata | Downloaded via `sweden.py` | Sweden sub-study provenance |
| `data/raw/sweden_slu_area_2022.json` | SLU PxWeb data response | Downloaded via `sweden.py` | `sweden.py::load_sweden_county_empirical_metrics()` |
| `data/raw/sweden_slu_increment_metadata.json` | SLU PxWeb metadata | Downloaded via `sweden.py` | Sweden sub-study provenance |
| `data/raw/sweden_slu_increment_2019.json` | SLU PxWeb data response | Downloaded via `sweden.py` | `sweden.py::load_sweden_county_empirical_metrics()` |
| `data/raw/sweden_slu_biomass_metadata.json` | SLU PxWeb metadata | Downloaded via `sweden.py` | Sweden sub-study provenance |
| `data/raw/sweden_slu_biomass_2022.json` | SLU PxWeb data response | Downloaded via `sweden.py` | `sweden.py::load_sweden_county_empirical_metrics()` |

## Processing lineage

### Country baseline

1. `load_land_use_inputs()` filters the FAOSTAT land-use bulk file to the configured EU country list and configured land-use variables.
2. `load_forestry_inputs()` filters the FAOSTAT forestry bulk file to the configured EU country list and configured forestry variables.
3. `load_crop_production_profile()` reads Eurostat crop JSON-stat values for cereals, pulses, potatoes, and vegetables and derives:
   - `selected_food_crop_area_kha`
   - `selected_food_production_kt`
   - `food_production_intensity_index`
4. `build_baseline_inputs()` merges those three tables on `country`, `country_code`, `iso3_code`.
5. `build_baseline_metrics()` derives area, carbon density, harvest intensity, wood-fuel share, biodiversity proxy, and the country-specific forest carbon opportunity-cost factor.

### NUTS-2 screening

1. `load_nuts2_geometries()` reads GISCO 2024 NUTS-2 geometry.
2. `load_nuts2_landcover_context()` reads Eurostat `lan_lcv_ovw` and derives woodland, cropland, grassland, feed-land, and permanent-crop context.
3. `build_nuts2_screening_dataset()` merges geometry and land cover by exact `nuts2_id`, then downscales country results by each region’s share of national woodland area.

### Sweden empirical case

1. `download_sweden_slu_raw_data()` downloads SLU metadata and table responses.
2. `load_sweden_county_empirical_metrics()` parses county-level area, increment, and biomass from the saved SLU responses.
3. `build_sweden_empirical_nuts2_case_study()` aggregates counties to NUTS-2, converts dry biomass to carbon, allocates Sweden’s national harvest profile by increment share, and reruns the forest scenario model region by region.

### Integrated policy and optimization layers

1. `build_regional_policy_options()` combines forest-option values with a stylized `Food-Land Safeguard`.
2. `select_regional_policy_priorities()` chooses the best unconstrained option per region.
3. `optimize_regional_policy_portfolio()` solves the constrained portfolio under biomass-supply and food-capacity safeguards.

## Current provenance strengths

- Raw files are separated from processed and derived files.
- Source URLs are declared in code.
- Eurostat and SLU JSON files embed source metadata and update timestamps.
- Methods docs explain most major transformations.

## Current provenance gaps

- No checksum manifest exists for raw files.
- No run manifest exists for processed and output artifacts.
- Eurostat status flags are not propagated into processed outputs.
- Exact NUTS-2 coverage losses are not published as a first-class artifact.
- Processed CSVs do not carry sidecar data dictionaries.

## Recommended next step

Add a machine-readable run manifest that records:

- raw file hashes
- provider update timestamps where available
- run timestamp
- parameter values
- Python/package versions
- output file list and hashes
