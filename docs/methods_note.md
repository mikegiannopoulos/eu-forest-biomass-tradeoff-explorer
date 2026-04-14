# Methods Note

## Objective

This project compares simplified forest biomass allocation scenarios across the EU to show how land-use carbon retention, biomass use, spatial screening, crop-production context, and a light economic framing can be combined in a transparent policy-style workflow. The latest extension adds a Sweden empirical sub-study based on official SLU county-level forest area, biomass, and increment data, plus a regional land-competition screen and a constrained NUTS-2 portfolio step so forest biomass decisions can be compared with a food-land safeguard under explicit biomass and food-capacity conditions.

## Spatial and Temporal Scope

- Spatial unit: EU-27 countries.
- Spatial geometry: Eurostat GISCO country polygons.
- Analysis year: 2024, the latest year shared by the FAOSTAT land-use and forestry inputs used here.

The project also includes NUTS-2 screening extensions:

- Spatial unit: EU NUTS-2 regions where Eurostat regional land-cover data are available.
- Spatial geometry: Eurostat GISCO NUTS-2 polygons.
- Regional land-cover year: 2022, the latest year available in the selected Eurostat regional land-cover dataset.
- Country crop-production context: Eurostat `apro_cpsh1` for 2024.

The Sweden empirical sub-study adds:

- Spatial unit: Swedish NUTS-2 regions.
- Forest area source: SLU Table 3.1a productive forest area by county, `2022` five-year average.
- Biomass source: SLU Table 3.29b tree dry weight biomass by county, `2022` five-year average.
- Increment source: SLU Table 3.31a annual volume increment by county, `2019` average year.
- Regionalization step: county values are aggregated to NUTS-2 using a transparent county-to-NUTS-2 lookup.

## System Boundary

The model tracks a limited land-use and biomass system boundary with five linked components:

1. `Land-use carbon context`
   Forest area and living biomass carbon stock are taken from FAOSTAT land-use statistics.

2. `Biomass allocation`
   Observed roundwood production is split into industrial roundwood and wood fuel using FAOSTAT forestry data.

3. `Climate-accounting comparison`
   Scenario deltas relative to baseline are calculated using:
   - forest carbon retention or opportunity cost,
   - substitution benefits,
   - supply-chain emission proxies.

4. `Regional land competition`
   A NUTS-2 extension uses observed cropland, grassland, fodder, and permanent-crop context to compare forest options with a stylized food-land safeguard. Country-level crop-production intensity from Eurostat is added to strengthen the agricultural side of the screen.

5. `Constrained regional portfolio`
   A small mixed-integer optimization chooses one policy per NUTS-2 region to maximize total climate value while enforcing minimum biomass-supply and food-capacity safeguards.

The Sweden sub-study sits between components 3 and 4. It replaces woodland-share downscaling with real subnational forest area, dry biomass, and annual increment for Swedish NUTS-2 regions, but still inherits Sweden's national harvested-wood product mix from FAOSTAT.

The model does not include downstream product lifetimes, forest age classes, direct regional agricultural emissions, trade leakage, or calibrated market equilibrium across sectors.

## Baseline Indicators

For each country, the pipeline derives:

- forest area in hectares,
- forest carbon stock in living biomass, converted from `Mt C` to `MtCO2e`,
- harvest intensity in `m3/ha`,
- wood fuel share in total roundwood production,
- sawnwood-to-industrial-roundwood ratio as a simple material-use efficiency proxy,
- share of naturally regenerating forest,
- share of planted forest,
- a biodiversity-pressure proxy:

```text
biodiversity_pressure_proxy =
  harvest_intensity_m3_per_ha * naturally_regenerating_share
```

This is not a biodiversity indicator. It is only a screening proxy intended to capture the idea that a given harvest intensity may imply greater ecological pressure where more forest area is naturally regenerating.

## Scenario Design

### Conservation Priority

- Total harvest is reduced by 15 percent.
- The reduction is taken from wood fuel first.
- Interpretation: a conservation-oriented policy that prioritizes retaining standing biomass rather than removing lower-value energy wood.

### Material Cascade

- Total harvest is unchanged.
- 20 percent of current wood fuel volume is reallocated to industrial roundwood uses.
- Interpretation: a cascade strategy that shifts existing biomass away from direct combustion and toward material use.

### Bioenergy Push

- Total harvest rises by 15 percent.
- The additional harvest is allocated to wood fuel.
- Interpretation: a more extraction-intensive bioenergy pathway.

## Climate Accounting Structure

The scenario model is explicitly simplified and designed for transparent comparison, not detailed inventory accounting.

For each country and scenario, the pipeline estimates:

### 1. Supply-chain savings

Differences in harvest and processing emissions are represented with fixed coefficients:

- material pathway: `0.08 tCO2e/m3`
- bioenergy pathway: `0.10 tCO2e/m3`

### 2. Substitution gain

Material and bioenergy uses are assigned different avoided-emissions proxies:

- material pathway: `1.10 tCO2e/m3`
- bioenergy pathway: `0.40 tCO2e/m3`

These are stylized portfolio coefficients, not claims about one universal displacement factor.

### 3. Forest carbon retention

The in-forest carbon effect is handled as an opportunity-cost term per cubic meter harvested. That factor is not constant across countries. It rises where observed harvest intensity and forest carbon stock density are higher:

```text
opportunity_cost_per_m3 =
  0.60
  + 0.14 * (harvest_intensity / EU_median_harvest_intensity - 1)
  + 0.10 * (carbon_density / EU_median_carbon_density - 1)
```

The result is clipped to the range `0.35` to `0.90 tCO2e/m3`.

This is proxy-based, but it keeps the carbon accounting tied to observed land-use conditions rather than using a single EU-average penalty.

## Sensitivity and Robustness Layer

To move the project beyond a single deterministic parameterization, the pipeline includes a fixed-seed sensitivity experiment with `400` parameter draws.

The following quantities are varied over predefined ranges:

- base forest carbon opportunity cost,
- harvest-pressure sensitivity,
- carbon-density sensitivity,
- material substitution benefit,
- bioenergy substitution benefit,
- material supply-chain emissions,
- bioenergy supply-chain emissions,
- conservation harvest reduction share,
- material-cascade shift share,
- bioenergy harvest increase share.

This robustness layer produces:

- EU-level uncertainty ranges for total scenario benefit,
- the frequency with which each scenario is the best EU-wide option,
- country-level modal best scenarios,
- country-level robustness shares showing how often each scenario is best.

This does not make the model fully validated, but it does make the interpretation much more credible because it distinguishes between recommendations that are stable and recommendations that depend on a narrow assumption set.

## NUTS-2 Screening Extension

The Europe-wide NUTS-2 layer is intentionally framed as a screening extension rather than a regional production model.

Observed directly at NUTS-2:

- total land area,
- woodland area,
- broadleaved woodland area,
- coniferous woodland area,
- mixed woodland area.
- cropland area,
- grassland area,
- fodder-crop area,
- temporary grassland area,
- permanent-crop area.

Not observed directly at NUTS-2 in this project:

- roundwood production,
- wood fuel production,
- industrial roundwood production,
- forest carbon stock.

To avoid overclaiming, country-level best-scenario outputs are downscaled to NUTS-2 in proportion to each region's share of national woodland area. The resulting regional score is therefore a spatial allocation and screening exercise, not an independent regional forest-sector estimate.

## Sweden Empirical Forest Sub-Study

To strengthen the weakest methodological point in the original NUTS-2 layer, the project adds a deeper Sweden case study that uses real subnational forest data from the Swedish National Forest Inventory instead of woodland-share downscaling.

Observed directly through SLU county tables:

- productive forest area,
- total tree dry biomass,
- mean annual volume increment.

These county values are aggregated to Swedish NUTS-2 regions. Dry biomass is converted to carbon stock using:

```text
forest_carbon_stock_mt_c =
  dry_biomass_million_t * 0.50
```

and then to `MtCO2e` using the same `44/12` conversion used elsewhere in the project.

The regional baseline forest input set is then constructed as follows:

- `forest area`: direct sum of county productive forest area,
- `forest carbon stock`: direct sum of county dry biomass converted to carbon,
- `harvest allocation`: Sweden's national FAOSTAT harvest is allocated to NUTS-2 regions in proportion to observed annual increment share,
- `wood product mix`: Sweden's national industrial-roundwood and wood-fuel split is retained for all Swedish regions,
- `naturally regenerating`, `planted`, and `primary` shares: Sweden's national FAOSTAT shares are applied to regional forest area because these specific stock splits are not observed directly in the selected SLU county tables.

This means the Sweden case is still not a complete regional forest-sector model, but it is materially stronger than woodland-share downscaling because the regional forest stock and supply context are now empirical.

## Integrated Forest-Versus-Food Policy Screen

The new regional allocation layer keeps the forest scenario engine unchanged and adds a separate NUTS-2 policy comparison.

For each NUTS-2 region, the workflow evaluates:

- the three forest options regionalized from country-level scenario results,
- one additional `Food-Land Safeguard` option.

The `Food-Land Safeguard` option is not a direct estimate of agricultural production or emissions. It is a proxy for the climate opportunity cost of diverting agricultural land into additional biomass supply.

The proxy is built in three steps:

1. Measure regional agricultural land context from Eurostat:
   - cropland share,
   - grassland share,
   - feed-land share,
   - permanent-crop share.

2. Add country-level crop-production intensity from Eurostat `apro_cpsh1`.

   The project extracts 2024 area, production, and yield data for cereals, pulses, potatoes, and vegetables, then builds a country-level `food_production_intensity_index` from relative yields across those crop groups.

3. Define a small marginal land-at-risk term:

```text
marginal_agricultural_land_ha =
  agricultural_land_area_ha * 0.05
```

4. Apply a bounded displacement-risk coefficient:

```text
food_land_displacement_proxy_tco2e_per_ha =
  0.30
  + 0.20 * feed_land_share_of_agricultural_land
  + 0.15 * permanent_crop_share_of_agricultural_land
  + 0.12 * (food_production_intensity_index - 1)
```

The result is clipped to `0.20` to `0.70 tCO2e/ha`.

To give the optimization step a simple food-side capacity metric, the workflow also computes:

```text
food_capacity_indexed_ha =
  marginal_agricultural_land_ha
  * cropland_share_of_agricultural_land
  * food_production_intensity_index
```

Regional policy comparison is then made using:

```text
policy_value_eur =
  policy_benefit_tco2e * EUR 100/tCO2
```

The selected NUTS-2 priority is first identified as the option with the highest value per hectare of total land.

## Constrained Regional Portfolio

The new optimization layer uses the same NUTS-2 option set, but instead of selecting each region independently it solves one EU-wide portfolio problem.

Decision variable:

- choose exactly one option for each NUTS-2 region.

Objective:

```text
maximize sum(policy_value_eur across all selected regional options)
```

Constraints:

```text
sum(regional_harvest_after_policy_m3) >= 0.97 * baseline_regionalized_harvest_m3
sum(food_capacity_indexed_ha) >= 0.22 * total_available_food_capacity_indexed_ha
```

This is still a screening optimization, not a calibrated partial-equilibrium or sector-coupling model. But it is useful because it forces the project to make trade-offs explicit instead of only reporting region-by-region best options.

The optimization layer itself still operates on the common Europe-wide NUTS-2 option structure. The Sweden empirical sub-study improves the forestry screening side directly and is reported alongside, rather than being presented as a full empirical re-estimation of every later integrated land-competition step.

## Net Climate Benefit

For each scenario, the model reports benefits relative to baseline:

```text
net_climate_benefit =
  supply_chain_savings
  + substitution_gain
  + forest_carbon_retention
```

Positive values indicate an improvement relative to observed 2024 biomass allocation.

## Economic Dimension

The light economic component is a carbon-price framing:

```text
carbon_value_eur = net_climate_benefit_tco2e * EUR 100/tCO2
carbon_value_eur_per_ha = carbon_value_eur / forest_area_ha
```

This is not a market equilibrium model or cost curve. It is a decision-support proxy showing how country rankings change when climate benefit is valued explicitly.

For the integrated regional screen, the same carbon-price framing is used to compare:

- regionalized forest-scenario value,
- food-land safeguard value for marginal agricultural land.

For the constrained portfolio, the same value metric becomes the optimization objective under explicit biomass and food-capacity safeguards.

## What Is Directly Observed vs Proxy-Based

### Observed from official data

- forest area,
- forest carbon stock in living biomass,
- naturally regenerating forest area,
- planted forest area,
- primary forest area where available,
- roundwood, industrial roundwood, wood fuel, sawnwood, and wood pellet production,
- crop area, production, and yield for selected food crop groups,
- EU country geometry,
- NUTS-2 geometry,
- NUTS-2 woodland, cropland, grassland, fodder, and permanent-crop land cover.

### Proxy-based

- supply-chain emission factors,
- substitution benefits,
- country-specific forest carbon opportunity-cost factor,
- biodiversity-pressure proxy,
- carbon-price valuation.
- food-capacity indexed hectares for the constrained portfolio,
- the food-land safeguard displacement proxy for marginal agricultural land.

## Why The Simplifications Are Acceptable Here

The point of the project is not to reproduce a sector model like ClimAg, CRAFT, or TERRAMARE. The point is to demonstrate:

- careful system-boundary definition,
- transparent assumptions,
- the ability to combine land-use and production statistics,
- spatial analysis and scenario comparison,
- a simple forest-versus-food land-competition framing,
- a small explicit biophysical-economic allocation step,
- uncertainty-aware interpretation,
- awareness of economic interpretation,
- honest communication of limits.

For a portfolio piece aimed at a land-use and climate PhD application, that is an appropriate and defensible scope.
