# Assumptions

## Data and Harmonization Assumptions

- The analysis year is fixed at 2024 because it is the latest year shared across the official FAOSTAT land-use and forestry variables used here.
- EU membership is taken from the Eurostat GISCO `EU_STAT` flag in the 2024 country geometry layer.
- FAOSTAT and GISCO are harmonized with a direct country lookup. The only special naming adjustment required in practice is `Netherlands` versus `Netherlands (Kingdom of the)`.
- `Roundwood` is treated as the sum of `Industrial roundwood` and `Wood fuel`. In the selected 2024 FAOSTAT data, the identities match exactly for the countries included here.
- The NUTS-2 screening extension uses Eurostat land-cover statistics from `2022`, because that is the latest year available in the selected regional land-cover dataset.
- The agricultural production context uses Eurostat `apro_cpsh1` for `2024` and is limited to cereals, pulses, potatoes, and vegetables.
- Regional scenario values are downscaled from country results in proportion to each region's share of national woodland area.
- The Sweden empirical sub-study uses official SLU county-level productive forest area and dry biomass for `2022` five-year averages, and annual increment for `2019`, then aggregates those county values to Swedish NUTS-2 regions.
- The integrated land-competition screen treats cropland and grassland as the relevant regional agricultural land base for a simplified food-and-feed safeguard.
- The constrained portfolio treats crop-capacity protection as a cropland-weighted intensity proxy, not as direct food output.

## Core Scenario Assumptions

| Parameter | Value | Use |
| --- | ---: | --- |
| Harvest reduction in conservation scenario | 15% | Conservation Priority |
| Share of wood fuel shifted to material use | 20% | Material Cascade |
| Harvest increase in bioenergy scenario | 15% | Bioenergy Push |
| Carbon price | EUR 100/tCO2 | Carbon-value ranking |

## Integrated Land-Competition Assumptions

| Parameter | Value | Use |
| --- | ---: | --- |
| Marginal agricultural land at risk | 5% of cropland + grassland | Food-Land Safeguard |
| Base food-land displacement proxy | 0.30 tCO2e/ha | Food-Land Safeguard |
| Feed-land sensitivity | 0.20 | Raises proxy in feed-heavy regions |
| Permanent-crop sensitivity | 0.15 | Raises proxy in permanent-crop regions |
| Food-production-intensity sensitivity | 0.12 | Raises proxy where crop yields are high |
| Food-land proxy bounds | 0.20 to 0.70 tCO2e/ha | Keeps the proxy in a conservative screening range |

## Sweden Empirical Sub-Study Assumptions

| Parameter | Value | Use |
| --- | ---: | --- |
| Productive forest area vintage | SLU `2022` five-year average | Sweden NUTS-2 empirical forest area |
| Dry biomass vintage | SLU `2022` five-year average | Sweden NUTS-2 empirical carbon stock |
| Annual increment vintage | SLU `2019` average year | Sweden NUTS-2 harvest allocation share |
| Dry biomass to carbon factor | 0.50 tC per t dry biomass | Biomass-to-carbon conversion |
| Regional harvest allocation rule | Sweden national harvest x regional increment share | Empirical supply proxy |
| Regional naturally regenerating share | Sweden national FAOSTAT share | Regional forest-type context proxy |
| Regional planted share | Sweden national FAOSTAT share | Regional forest-type context proxy |
| Regional primary-forest share | Sweden national FAOSTAT share | Regional forest-type context proxy |

## Constrained Portfolio Assumptions

| Parameter | Value | Use |
| --- | ---: | --- |
| Biomass-supply floor | 97% of baseline regionalized harvest | Constrained NUTS-2 portfolio |
| Food-capacity floor | 22% of total available indexed crop-capacity safeguard | Constrained NUTS-2 portfolio |

## Sensitivity Ranges

The robustness workflow varies the main proxy parameters across predefined exploratory ranges:

| Parameter | Range |
| --- | ---: |
| Base forest carbon opportunity cost | 0.45 to 0.75 tCO2e/m3 |
| Harvest-pressure sensitivity | 0.08 to 0.22 |
| Carbon-density sensitivity | 0.05 to 0.15 |
| Material substitution benefit | 0.90 to 1.30 tCO2e/m3 |
| Bioenergy substitution benefit | 0.20 to 0.60 tCO2e/m3 |
| Material supply-chain emissions | 0.05 to 0.10 tCO2e/m3 |
| Bioenergy supply-chain emissions | 0.10 to 0.16 tCO2e/m3 |
| Conservation harvest reduction | 10% to 20% |
| Material-cascade shift share | 10% to 30% |
| Bioenergy harvest increase | 10% to 25% |

These are not claimed to be literature-calibrated probability distributions. They are structured stress-test ranges chosen to examine whether the qualitative conclusions survive reasonable changes in the model assumptions.

## Proxy Coefficients

| Coefficient | Value | Interpretation |
| --- | ---: | --- |
| Material substitution benefit | 1.10 tCO2e/m3 | Avoided-emissions proxy for material use |
| Bioenergy substitution benefit | 0.40 tCO2e/m3 | Avoided-emissions proxy for direct energy use |
| Material supply-chain emissions | 0.08 tCO2e/m3 | Harvest and processing proxy |
| Bioenergy supply-chain emissions | 0.10 tCO2e/m3 | Harvest and processing proxy |
| Base forest carbon opportunity cost | 0.60 tCO2e/m3 | Starting point before country adjustment |
| Minimum opportunity cost | 0.35 tCO2e/m3 | Lower bound |
| Maximum opportunity cost | 0.90 tCO2e/m3 | Upper bound |

## Country-Specific Carbon Opportunity Cost

The forest carbon opportunity-cost proxy is increased where:

- harvest intensity is above the EU median,
- forest carbon stock density is above the EU median.

This is intentionally simple, but it captures an important systems insight: removing one cubic meter of wood is not equally consequential in all landscapes.

## Interpretation Assumptions

- A `positive` net climate benefit means the scenario performs better than the observed 2024 baseline.
- A `positive` carbon value per hectare means the scenario has positive climate value under the stated carbon-price assumption.
- The biodiversity-pressure proxy is a screening device, not an ecological outcome measure.
- A high `share_best` in the sensitivity outputs is interpreted as a robustness signal, not as a formal probability that a policy is optimal in the real world.
- A `Food-Land Safeguard` recommendation means the stylized agricultural land-retention value exceeds the best forest-option value in that region under the stated proxy assumptions.
- In the constrained portfolio, a region may be assigned a lower-value local option if that helps satisfy the EU-wide biomass-supply or food-capacity safeguards.
- In the Sweden empirical sub-study, regional forest area, biomass, and increment are treated as measured, but harvested product composition is still inherited from the Sweden national baseline.

## Why These Assumptions Were Chosen

The project is designed to show rigorous thinking under tight portfolio constraints:

- use real official data where possible,
- keep proxy assumptions explicit and inspectable,
- avoid pretending to have dynamic forest growth, product pools, or trade equilibrium when those are not actually modeled,
- produce outputs that can still support a serious conversation about land-use and biomass policy trade-offs.
