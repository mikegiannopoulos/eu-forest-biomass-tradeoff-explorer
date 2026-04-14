# Short Research Report

## Title

**EU forest biomass allocation, food-land competition, and a Sweden empirical sub-study under uncertainty**

## Abstract

This project develops a reproducible EU-wide screening model to compare three forest biomass pathways: reducing harvest for conservation, shifting existing wood fuel toward material use, and increasing harvest for bioenergy. The baseline analysis combines FAOSTAT land-use and forestry statistics with Eurostat GISCO country geometry. The model estimates scenario differences using three transparent components: forest carbon opportunity cost, substitution benefits, and supply-chain emissions proxies. A fixed-seed sensitivity analysis with 400 parameter draws is then used to assess robustness. The project then adds three Europe-wide NUTS-2 extensions using official Eurostat regional land-cover and crop-production data: a woodland screening layer, an integrated policy screen that compares the best forest option with a food-land safeguard for marginal cropland and grassland, and a constrained portfolio that chooses one policy per region under EU-wide biomass-supply and food-capacity safeguards. To strengthen the weakest part of that regional layer, the project also adds a Sweden empirical sub-study that aggregates official SLU county-level forest area, dry biomass, and annual increment to Swedish NUTS-2 regions and reruns the forest scenario model region by region. Across the baseline runs, material cascade and conservation priority both outperform bioenergy expansion. Under sensitivity testing, material cascade is the best EU-wide scenario in 56% of runs and conservation priority in 44%, while bioenergy push never becomes the best EU-wide option. In the unconstrained integrated NUTS-2 screen, material cascade is selected in 92 regions, conservation in 79, and the food-land safeguard in 40. In the constrained portfolio, material cascade rises to 123 regions, conservation falls to 34, and the food-land safeguard rises to 54 while retaining roughly 97.0% of baseline regionalized biomass supply and safeguarding 45.6% of the available crop-capacity proxy. In the Sweden empirical sub-study, all 8 Swedish NUTS-2 regions favor material cascade, but the empirical regional value profile differs materially from the woodland-share screen, especially in southern versus northern Sweden. The results show policy-relevant structure, meaningful uncertainty, and a credible first step toward the style of biophysical-economic land-use modeling described in the Chalmers PhD advertisement.

## 1. Motivation

European land-use and climate policy increasingly has to balance several goals at once:

- maintain or increase forest carbon stocks,
- supply biomass for materials and energy,
- avoid simplistic assumptions that all bioenergy is climate-beneficial,
- recognize spatial heterogeneity in forested landscapes.

This repository was built as a smaller, transparent project to demonstrate those research instincts without pretending to replicate a full integrated assessment or forest sector optimization model.

## 2. Data

The core country-level analysis uses:

- FAOSTAT land-use statistics for forest area and living biomass carbon stock,
- FAOSTAT forestry production statistics for roundwood, industrial roundwood, wood fuel, sawnwood, and wood pellets,
- Eurostat GISCO country boundaries.

The new subnational extension uses:

- Eurostat GISCO NUTS-2 geometry,
- Eurostat `lan_lcv_ovw` regional land-cover statistics for woodland, cropland, grassland, fodder, and permanent-crop context.
- Eurostat `apro_cpsh1` crop statistics for selected food crop area, production, and yield.
- SLU Swedish National Forest Inventory PxWeb tables for county-level productive forest area, dry biomass, and annual increment, aggregated here to Swedish NUTS-2 regions.

## 3. Methods

### 3.1 Country-level scenario model

The country model compares:

- `Conservation Priority`
- `Material Cascade`
- `Bioenergy Push`

Scenario deltas relative to baseline are decomposed into:

- forest carbon retention,
- substitution gain,
- supply-chain savings.

The project uses a country-specific forest carbon opportunity-cost factor rather than a single EU average.

### 3.2 Robustness layer

To avoid relying on one fixed parameterization, the model runs 400 deterministic sensitivity draws over key carbon-accounting and scenario-intensity assumptions. This makes it possible to ask:

- which scenario wins most often EU-wide,
- which countries have stable recommendations,
- which countries are borderline.

### 3.3 NUTS-2 screening extension

The project does **not** claim to observe forestry production directly at NUTS-2. Instead, it creates an explicitly labeled regional screening layer:

- official regional woodland area and composition are measured directly from Eurostat land-cover statistics,
- country-level scenario results are downscaled to NUTS-2 in proportion to each region's share of national woodland area,
- a `screening priority score` combines regionalized scenario value, woodland share, and country-level robustness.

This gives a more detailed spatial view while remaining honest about the data boundary.

### 3.4 Sweden empirical forest sub-study

The main methodological upgrade in the current version is a Sweden subset where the regional forest screening is no longer based only on woodland-share downscaling.

Using official SLU county tables, the project observes directly:

- productive forest area,
- total tree dry biomass,
- mean annual volume increment.

These county values are aggregated to Swedish NUTS-2 regions. Dry biomass is converted to forest carbon stock with a fixed `0.50 tC/t dry biomass` factor. Sweden's national FAOSTAT harvest is then allocated across those NUTS-2 regions in proportion to observed annual increment share, and the same forest scenario model is rerun for each Swedish region using:

- empirical regional forest area,
- empirical regional biomass-derived carbon stock,
- increment-based regional harvest allocation,
- Sweden's national harvested-wood product mix.

This is still not a fully observed regional forest-sector model, but it is a substantial methodological upgrade over pure woodland-share screening.

### 3.5 Integrated forest-versus-food screen

The newest extension adds a fourth regional option: `Food-Land Safeguard`.

This option is intentionally simple. It does not estimate agricultural greenhouse gases directly. Instead, it assigns a climate opportunity value to retaining a small marginal share of agricultural land in regions where:

- cropland and grassland shares are high,
- feed-land shares are high,
- permanent crops are present.

To make that agricultural side more defensible than a pure land-cover proxy, the project also adds a country-level `food_production_intensity_index` from official Eurostat crop statistics for cereals, pulses, potatoes, and vegetables.

The integrated NUTS-2 recommendation is then the highest-value option among:

- conservation priority,
- material cascade,
- bioenergy push,
- food-land safeguard.

### 3.6 Constrained regional portfolio

The final extension solves a small mixed-integer allocation problem over the NUTS-2 option set.

The objective is to maximize total regional policy value while enforcing two EU-wide safeguards:

- retain at least `97%` of baseline regionalized biomass supply,
- safeguard at least `22%` of available crop-capacity proxy.

This is still a screening model rather than a full land-use or forest-sector optimization framework, but it is materially closer to the “biophysical and economic models” language in the advertised PhD than a simple region-by-region ranking.

## 4. Results

### 4.1 Country-level baseline findings

Under the default parameterization:

- `Material Cascade` improves EU climate performance by about `18.4 MtCO2e` relative to the observed baseline.
- `Conservation Priority` improves EU climate performance by about `17.1 MtCO2e`.
- `Bioenergy Push` is strongly negative at about `-21.8 MtCO2e`.

This is already a useful result because it shows that diverting wood away from direct combustion often performs better than expanding bioenergy extraction.

### 4.2 Robustness findings

The sensitivity analysis changes the interpretation from “what wins once” to “what wins often.”

EU-wide:

- `Material Cascade` is best in `56%` of runs.
- `Conservation Priority` is best in `44%` of runs.
- `Bioenergy Push` is never best.

Country-level robustness is uneven:

- highly robust toward conservation: Belgium, Czechia, Poland
- highly robust toward material cascade: Cyprus, Greece, Italy, France
- more assumption-sensitive: Spain, Romania, Lithuania, Portugal, Finland

That pattern is analytically useful because it shows where the project produces strong directional evidence and where it produces a conditional recommendation instead.

### 4.3 NUTS-2 screening findings

The NUTS-2 extension identifies where the regional concentration of forest-relevant scenario value is strongest once woodland presence and country-level robustness are considered together.

The highest-scoring regions in the current screening include:

- Bourgogne and Franche-Comté in France,
- several forest-relevant German NUTS-2 regions such as Weser-Ems and Lüneburg,
- Estonia as a whole at NUTS-2 level,
- parts of western and central France with high woodland shares.

These are not claims that the regional policy answer has been estimated directly from regional forestry production data. They are spatial screening results showing where the country-level scenario signal is most concentrated in regional woodland landscapes.

### 4.4 Sweden empirical sub-study findings

The Sweden empirical rerun adds a more defensible regional forest layer than the generic Europe-wide screen.

Key results:

- all `8` Swedish NUTS-2 regions select `Material Cascade` under the default parameterization,
- the empirical land-value signal is weaker than the original woodland-share screen in `SE12`, `SE21`, and especially `SE22`,
- the empirical signal is stronger in northern Sweden, especially `SE31`, `SE32`, and `SE33`.

The most notable difference appears in `SE22 Sydsverige`, where the original woodland-share screen implied roughly `EUR 8.6/ha` of total land but the empirical SLU-based rerun gives about `EUR 1.6/ha` of total land and `EUR 5.33/forest ha` for the best forest scenario. This matters because it shows that a real subnational forest stock and increment layer can change the spatial ranking even when the broad policy preference remains the same. It also helps explain why SE22 can still select `Food-Land Safeguard` in the integrated map: the Sweden rerun is forest-only and ranked on a forest-hectare basis, while the integrated screen compares forest plus food-land options on a total-land basis.

### 4.5 Integrated forest-versus-food findings

Once agricultural land competition is made explicit at NUTS-2 level:

- `Material Cascade` remains the most common selected regional priority with `92` regions,
- `Conservation Priority` is selected in `79` regions,
- `Food-Land Safeguard` becomes the preferred option in `40` regions,
- `Bioenergy Push` is not selected in any region.

The strongest food-land safeguard signals appear in agricultural or mixed landscapes where regional agricultural land shares are high and forest-option value is relatively modest, including Malta, Cyprus, parts of France, Greece, Spain, Belgium, and the western Netherlands.

### 4.6 Constrained portfolio findings

Once the optimizer enforces EU-wide biomass and food safeguards:

- `Material Cascade` rises to `123` selected regions,
- `Conservation Priority` falls to `34`,
- `Food-Land Safeguard` rises to `54`,
- `Bioenergy Push` is still not selected anywhere.

In total, `45` NUTS-2 regions switch away from their unconstrained best option. The model retains about `97.0%` of baseline regionalized harvest while safeguarding about `45.6%` of the available crop-capacity proxy, well above the minimum `22%` requirement. The optimized portfolio has a total value of about `EUR 2.15 billion` at `EUR 100/tCO2`.

## 5. Interpretation

Three conclusions are especially relevant for a land-use and climate application:

1. The project distinguishes between land-carbon effects and downstream substitution effects rather than collapsing them into one number.
2. It shows that material use and conservation can both outperform direct bioenergy expansion, depending on context.
3. It shows that replacing woodland-share downscaling with real Swedish subnational forest data changes the regional signal in meaningful ways, especially between southern and northern Sweden.
4. It shows that some subnational regions are better framed as food-land safeguards than as forest-biomass interventions once land competition is represented.
5. It goes one step further and forces those regional choices through an EU-wide constrained portfolio problem, which is much closer to actual policy design.
6. It treats uncertainty as part of the result rather than as an afterthought.

## 6. Limitations

- Country-level scenario accounting remains simpler than a full forest-sector model.
- Most NUTS-2 layers are still screening extensions, not direct regional forestry or agricultural production models, although the Sweden subset now uses official subnational forest area, biomass, and increment data.
- Parameter uncertainty is explored through ranges, not formal posterior calibration.
- Biodiversity remains proxy-based, and the food side still uses country-level crop-intensity transfer rather than regional agricultural GHG accounting.
- The Sweden empirical case still inherits Sweden's national product mix and does not yet include observed regional harvest removals or harvested wood product pools.

## 7. Why This Matters For The Portfolio

This report makes the repository look much more like early doctoral work because it now includes:

- a clear research question,
- reproducible data and code,
- scenario comparison,
- robustness analysis,
- regional spatial extension,
- one empirical subnational forestry subset rather than only downscaled regional screening,
- explicit forest-versus-food land competition,
- a constrained regional allocation layer,
- and a documented link between assumptions and published literature.

That combination is much closer to applied environmental systems analysis than to generic climate visualization.
