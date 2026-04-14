from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "figures"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

ANALYSIS_YEAR = 2024
CARBON_PRICE_EUR_PER_TCO2 = 100.0


@dataclass(frozen=True)
class CountryConfig:
    country: str
    country_code: str
    iso3_code: str
    faostat_area: str


@dataclass(frozen=True)
class ScenarioDefinition:
    name: str
    label: str
    description: str


EU_COUNTRIES: tuple[CountryConfig, ...] = (
    CountryConfig("Austria", "AT", "AUT", "Austria"),
    CountryConfig("Belgium", "BE", "BEL", "Belgium"),
    CountryConfig("Bulgaria", "BG", "BGR", "Bulgaria"),
    CountryConfig("Croatia", "HR", "HRV", "Croatia"),
    CountryConfig("Cyprus", "CY", "CYP", "Cyprus"),
    CountryConfig("Czechia", "CZ", "CZE", "Czechia"),
    CountryConfig("Denmark", "DK", "DNK", "Denmark"),
    CountryConfig("Estonia", "EE", "EST", "Estonia"),
    CountryConfig("Finland", "FI", "FIN", "Finland"),
    CountryConfig("France", "FR", "FRA", "France"),
    CountryConfig("Germany", "DE", "DEU", "Germany"),
    CountryConfig("Greece", "EL", "GRC", "Greece"),
    CountryConfig("Hungary", "HU", "HUN", "Hungary"),
    CountryConfig("Ireland", "IE", "IRL", "Ireland"),
    CountryConfig("Italy", "IT", "ITA", "Italy"),
    CountryConfig("Latvia", "LV", "LVA", "Latvia"),
    CountryConfig("Lithuania", "LT", "LTU", "Lithuania"),
    CountryConfig("Luxembourg", "LU", "LUX", "Luxembourg"),
    CountryConfig("Malta", "MT", "MLT", "Malta"),
    CountryConfig("Netherlands", "NL", "NLD", "Netherlands (Kingdom of the)"),
    CountryConfig("Poland", "PL", "POL", "Poland"),
    CountryConfig("Portugal", "PT", "PRT", "Portugal"),
    CountryConfig("Romania", "RO", "ROU", "Romania"),
    CountryConfig("Slovakia", "SK", "SVK", "Slovakia"),
    CountryConfig("Slovenia", "SI", "SVN", "Slovenia"),
    CountryConfig("Spain", "ES", "ESP", "Spain"),
    CountryConfig("Sweden", "SE", "SWE", "Sweden"),
)

SCENARIOS: tuple[ScenarioDefinition, ...] = (
    ScenarioDefinition(
        name="baseline",
        label="Baseline",
        description="Observed 2024 forest biomass allocation from FAOSTAT.",
    ),
    ScenarioDefinition(
        name="conservation_priority",
        label="Conservation Priority",
        description=(
            "Reduce total harvest by 15 percent, taking the cut from wood fuel first "
            "to emulate a conservation-first policy that protects standing biomass."
        ),
    ),
    ScenarioDefinition(
        name="material_cascade",
        label="Material Cascade",
        description=(
            "Keep harvest volume constant but shift 20 percent of wood fuel volume "
            "into industrial roundwood uses."
        ),
    ),
    ScenarioDefinition(
        name="bioenergy_push",
        label="Bioenergy Push",
        description=(
            "Increase total harvest by 15 percent and allocate the extra harvest "
            "to direct energy use."
        ),
    ),
)

RAW_DATASETS = {
    "land_use": {
        "filename": "Inputs_LandUse_E_All_Data_(Normalized).zip",
        "url": "https://fenixservices.fao.org/faostat/static/bulkdownloads/Inputs_LandUse_E_All_Data_(Normalized).zip",
    },
    "forestry": {
        "filename": "Forestry_E_All_Data_(Normalized).zip",
        "url": "https://fenixservices.fao.org/faostat/static/bulkdownloads/Forestry_E_All_Data_(Normalized).zip",
    },
    "gisco_countries": {
        "filename": "CNTR_RG_20M_2024_4326.geojson",
        "url": "https://gisco-services.ec.europa.eu/distribution/v2/countries/geojson/CNTR_RG_20M_2024_4326.geojson",
    },
    "gisco_nuts2": {
        "filename": "NUTS_RG_20M_2024_4326_LEVL_2.geojson",
        "url": "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2024_4326_LEVL_2.geojson",
    },
    "eurostat_nuts2_landcover": {
        "filename": "lan_lcv_ovw.json",
        "url": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lan_lcv_ovw?lang=EN",
    },
    "eurostat_crop_production": {
        "filename": "apro_cpsh1_selected_2024.json",
        "url": (
            "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/apro_cpsh1"
            "?lang=EN&time=2024"
            "&geo=AT&geo=BE&geo=BG&geo=HR&geo=CY&geo=CZ&geo=DK&geo=EE&geo=FI&geo=FR&geo=DE"
            "&geo=EL&geo=HU&geo=IE&geo=IT&geo=LV&geo=LT&geo=LU&geo=MT&geo=NL&geo=PL&geo=PT"
            "&geo=RO&geo=SK&geo=SI&geo=ES&geo=SE"
            "&crops=C0000&crops=P0000&crops=R1000&crops=V0000"
            "&strucpro=AR&strucpro=PR_HU_EU&strucpro=YI_HU_EU"
        ),
    },
    "sweden_slu_area_metadata": {
        "filename": "sweden_slu_area_metadata.json",
    },
    "sweden_slu_area_data": {
        "filename": "sweden_slu_area_2022.json",
    },
    "sweden_slu_increment_metadata": {
        "filename": "sweden_slu_increment_metadata.json",
    },
    "sweden_slu_increment_data": {
        "filename": "sweden_slu_increment_2019.json",
    },
    "sweden_slu_biomass_metadata": {
        "filename": "sweden_slu_biomass_metadata.json",
    },
    "sweden_slu_biomass_data": {
        "filename": "sweden_slu_biomass_2022.json",
    },
}

SWEDEN_SLU_API_BASE_URL = "https://skogsstatistik.slu.se/api/v1/en/OffStat/ProduktivSkogsmark"
SWEDEN_SLU_TABLES = {
    "area": {
        "path": "Areal/PS_Areal_bestandstyper_tab_a.px",
        "metadata_dataset": "sweden_slu_area_metadata",
        "data_dataset": "sweden_slu_area_data",
        "year_variable_text": "Year (Five year average)",
        "year_value_text": "2022",
        "fixed_selections": {
            "Table contents": "Area (1000 ha)",
            "Forest type": "All forest types",
        },
        "value_column": "productive_forest_area_kha",
    },
    "increment": {
        "path": "Tillvaxt/PS_Tillvaxt_a_tab.px",
        "metadata_dataset": "sweden_slu_increment_metadata",
        "data_dataset": "sweden_slu_increment_data",
        "year_variable_text": "Year (Average)",
        "year_value_text": "2019",
        "fixed_selections": {
            "Table contents": "Annual increment (10000 m³sk)",
            "Tree species": "All tree species",
        },
        "value_column": "annual_increment_10000_m3sk",
    },
    "biomass": {
        "path": "Virkesforrad/PS_Virkesf_tradbiom_b_tab.px",
        "metadata_dataset": "sweden_slu_biomass_metadata",
        "data_dataset": "sweden_slu_biomass_data",
        "year_variable_text": "Year (Five year average)",
        "year_value_text": "2022",
        "fixed_selections": {
            "Table contents": "Million tonnes dry weight",
            "Tree fraction": "Total biomass",
            "Protected areas": "Incl. formally protected areas",
        },
        "value_column": "total_biomass_million_t_dry",
    },
}

SWEDEN_COUNTY_TO_NUTS2 = {
    "Stockholms län": "SE11",
    "Uppsala län": "SE12",
    "Södermanlands län": "SE12",
    "Östergötlands län": "SE12",
    "Örebro län": "SE12",
    "Västmanlands län": "SE12",
    "Jönköpings län": "SE21",
    "Kronobergs län": "SE21",
    "Kalmar län": "SE21",
    "Gotlands län": "SE21",
    "Blekinge län": "SE22",
    "Skåne län": "SE22",
    "Hallands län": "SE23",
    "Västra Götalands län": "SE23",
    "Värmlands län": "SE23",
    "Dalarnas län": "SE31",
    "Gävleborgs län": "SE31",
    "Västernorrlands län": "SE32",
    "Jämtlands län": "SE32",
    "Västerbottens län": "SE33",
    "Norrbottens län": "SE33",
}

SWEDEN_BIOMASS_CARBON_FRACTION = 0.50

LAND_USE_VARIABLES = (
    ("Forest land", "Area", "forest_area_kha"),
    ("Forest land", "Carbon stock in living biomass", "forest_carbon_stock_mt_c"),
    ("Naturally regenerating forest", "Area", "naturally_regenerating_forest_kha"),
    ("Planted Forest", "Area", "planted_forest_kha"),
    ("Primary Forest", "Area", "primary_forest_kha"),
)

FORESTRY_VARIABLES = (
    ("Roundwood", "Production", "roundwood_m3"),
    ("Industrial roundwood", "Production", "industrial_roundwood_m3"),
    ("Wood fuel", "Production", "wood_fuel_m3"),
    ("Sawnwood", "Production", "sawnwood_m3"),
    ("Wood pellets", "Production", "wood_pellets_t"),
)

BASE_FOREST_CARBON_OPPORTUNITY_COST_TCO2E_PER_M3 = 0.60
PRESSURE_SENSITIVITY = 0.14
CARBON_DENSITY_SENSITIVITY = 0.10
MIN_FOREST_CARBON_OPPORTUNITY_COST_TCO2E_PER_M3 = 0.35
MAX_FOREST_CARBON_OPPORTUNITY_COST_TCO2E_PER_M3 = 0.90

SUBSTITUTION_MATERIAL_TCO2E_PER_M3 = 1.10
SUBSTITUTION_BIOENERGY_TCO2E_PER_M3 = 0.40
SUPPLY_CHAIN_MATERIAL_TCO2E_PER_M3 = 0.08
SUPPLY_CHAIN_BIOENERGY_TCO2E_PER_M3 = 0.10

HARVEST_REDUCTION_SHARE = 0.15
WOOD_FUEL_TO_MATERIAL_SHIFT_SHARE = 0.20
HARVEST_INCREASE_SHARE = 0.15

MARGINAL_AGRICULTURAL_LAND_REALLOCATION_SHARE = 0.05
BASE_FOOD_LAND_DISPLACEMENT_TCO2E_PER_HA = 0.30
FEED_LAND_DISPLACEMENT_SENSITIVITY = 0.20
PERMANENT_CROP_DISPLACEMENT_SENSITIVITY = 0.15
FOOD_PRODUCTION_INTENSITY_SENSITIVITY = 0.12
MIN_FOOD_LAND_DISPLACEMENT_TCO2E_PER_HA = 0.20
MAX_FOOD_LAND_DISPLACEMENT_TCO2E_PER_HA = 0.70

OPTIMIZATION_BIOMASS_SUPPLY_FLOOR_SHARE = 0.97
OPTIMIZATION_FOOD_CAPACITY_FLOOR_SHARE = 0.22

SENSITIVITY_SAMPLE_SIZE = 400
SENSITIVITY_RANDOM_SEED = 42

SENSITIVITY_PARAMETER_RANGES = {
    "base_forest_carbon_opportunity_cost_tco2e_per_m3": (0.45, 0.75),
    "pressure_sensitivity": (0.08, 0.22),
    "carbon_density_sensitivity": (0.05, 0.15),
    "substitution_material_tco2e_per_m3": (0.90, 1.30),
    "substitution_bioenergy_tco2e_per_m3": (0.20, 0.60),
    "supply_chain_material_tco2e_per_m3": (0.05, 0.10),
    "supply_chain_bioenergy_tco2e_per_m3": (0.10, 0.16),
    "harvest_reduction_share": (0.10, 0.20),
    "wood_fuel_to_material_shift_share": (0.10, 0.30),
    "harvest_increase_share": (0.10, 0.25),
}


@dataclass(frozen=True)
class ModelParameters:
    carbon_price_eur_per_tco2: float
    base_forest_carbon_opportunity_cost_tco2e_per_m3: float
    pressure_sensitivity: float
    carbon_density_sensitivity: float
    min_forest_carbon_opportunity_cost_tco2e_per_m3: float
    max_forest_carbon_opportunity_cost_tco2e_per_m3: float
    substitution_material_tco2e_per_m3: float
    substitution_bioenergy_tco2e_per_m3: float
    supply_chain_material_tco2e_per_m3: float
    supply_chain_bioenergy_tco2e_per_m3: float
    harvest_reduction_share: float
    wood_fuel_to_material_shift_share: float
    harvest_increase_share: float


@dataclass(frozen=True)
class AllocationParameters:
    carbon_price_eur_per_tco2: float
    marginal_agricultural_land_reallocation_share: float
    base_food_land_displacement_tco2e_per_ha: float
    feed_land_displacement_sensitivity: float
    permanent_crop_displacement_sensitivity: float
    food_production_intensity_sensitivity: float
    min_food_land_displacement_tco2e_per_ha: float
    max_food_land_displacement_tco2e_per_ha: float


@dataclass(frozen=True)
class OptimizationParameters:
    biomass_supply_floor_share: float
    food_capacity_floor_share: float


DEFAULT_MODEL_PARAMETERS = ModelParameters(
    carbon_price_eur_per_tco2=CARBON_PRICE_EUR_PER_TCO2,
    base_forest_carbon_opportunity_cost_tco2e_per_m3=BASE_FOREST_CARBON_OPPORTUNITY_COST_TCO2E_PER_M3,
    pressure_sensitivity=PRESSURE_SENSITIVITY,
    carbon_density_sensitivity=CARBON_DENSITY_SENSITIVITY,
    min_forest_carbon_opportunity_cost_tco2e_per_m3=MIN_FOREST_CARBON_OPPORTUNITY_COST_TCO2E_PER_M3,
    max_forest_carbon_opportunity_cost_tco2e_per_m3=MAX_FOREST_CARBON_OPPORTUNITY_COST_TCO2E_PER_M3,
    substitution_material_tco2e_per_m3=SUBSTITUTION_MATERIAL_TCO2E_PER_M3,
    substitution_bioenergy_tco2e_per_m3=SUBSTITUTION_BIOENERGY_TCO2E_PER_M3,
    supply_chain_material_tco2e_per_m3=SUPPLY_CHAIN_MATERIAL_TCO2E_PER_M3,
    supply_chain_bioenergy_tco2e_per_m3=SUPPLY_CHAIN_BIOENERGY_TCO2E_PER_M3,
    harvest_reduction_share=HARVEST_REDUCTION_SHARE,
    wood_fuel_to_material_shift_share=WOOD_FUEL_TO_MATERIAL_SHIFT_SHARE,
    harvest_increase_share=HARVEST_INCREASE_SHARE,
)


DEFAULT_ALLOCATION_PARAMETERS = AllocationParameters(
    carbon_price_eur_per_tco2=CARBON_PRICE_EUR_PER_TCO2,
    marginal_agricultural_land_reallocation_share=MARGINAL_AGRICULTURAL_LAND_REALLOCATION_SHARE,
    base_food_land_displacement_tco2e_per_ha=BASE_FOOD_LAND_DISPLACEMENT_TCO2E_PER_HA,
    feed_land_displacement_sensitivity=FEED_LAND_DISPLACEMENT_SENSITIVITY,
    permanent_crop_displacement_sensitivity=PERMANENT_CROP_DISPLACEMENT_SENSITIVITY,
    food_production_intensity_sensitivity=FOOD_PRODUCTION_INTENSITY_SENSITIVITY,
    min_food_land_displacement_tco2e_per_ha=MIN_FOOD_LAND_DISPLACEMENT_TCO2E_PER_HA,
    max_food_land_displacement_tco2e_per_ha=MAX_FOOD_LAND_DISPLACEMENT_TCO2E_PER_HA,
)


DEFAULT_OPTIMIZATION_PARAMETERS = OptimizationParameters(
    biomass_supply_floor_share=OPTIMIZATION_BIOMASS_SUPPLY_FLOOR_SHARE,
    food_capacity_floor_share=OPTIMIZATION_FOOD_CAPACITY_FLOOR_SHARE,
)
