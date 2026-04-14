# Application Brief

## Title

**European forest carbon, wood-use, and food-land trade-offs under constrained regional policy design**

## Position Relevance

This project was developed as a portfolio-scale research exercise directly aligned with the Chalmers doctoral position `Doctoral student in Land Use and Climate Impacts`. The position asks for biophysical and economic modeling of greenhouse gas emissions from forest and agricultural systems, analysis of trade-offs between wood, food, energy, and conservation, and work at both European and sub-national scales. This repository is a smaller and deliberately transparent version of that type of work. It does not claim to reproduce the ClimAg, CRAFT, or TERRAMARE frameworks. Instead, it shows the applicant’s ability to formulate a land-use systems question, assemble official European datasets, build a defensible carbon-accounting workflow, analyze spatial heterogeneity, and express results in a policy-relevant way.

## Research Question

How do alternative forest-biomass strategies across Europe compare when climate performance is evaluated through forest carbon retention, substitution effects, and biomass use, and how do those forestry choices interact with agricultural land that may be important for food-related production capacity?

The project examines three stylized forest-biomass pathways:

- `Conservation Priority`: reduce total harvest by 15 percent, taking the reduction from wood fuel first.
- `Material Cascade`: keep harvest constant but shift 20 percent of wood fuel volume into industrial roundwood uses.
- `Bioenergy Push`: increase total harvest by 15 percent and allocate the additional harvest to direct energy use.

It then adds a fourth NUTS-2 policy option:

- `Food-Land Safeguard`: assign climate value to retaining a marginal share of agricultural land against additional biomass diversion.

Finally, the project asks a more policy-relevant question: if Europe wants to maintain biomass supply while also safeguarding food-related land capacity, what regional portfolio of policies should be selected?

## Data and Spatial Scope

The workflow combines official European and FAO data sources:

- FAOSTAT land-use statistics for forest area and living biomass carbon stock,
- FAOSTAT forestry statistics for roundwood, industrial roundwood, wood fuel, and sawnwood production,
- Eurostat GISCO country geometry,
- Eurostat GISCO NUTS-2 geometry,
- Eurostat `lan_lcv_ovw` regional land-cover statistics for woodland, cropland, grassland, fodder, and permanent crops,
- Eurostat `apro_cpsh1` crop statistics for selected food crop area, production, and yield.

The country-level analysis uses 2024, the latest year shared across the selected FAOSTAT inputs. The NUTS-2 land-cover layer uses 2022 because that is the latest year available in the chosen Eurostat regional dataset. The study domain is the EU-27, with a spatial extension to NUTS-2 regions where the Eurostat land-cover data are available.

## Methods

The country-level model starts from observed forest area, living biomass carbon stock, and wood-harvest composition. For each scenario, it estimates a climate effect relative to baseline through three transparent components:

- `Forest carbon retention`: avoided forest carbon opportunity cost when harvest falls relative to baseline,
- `Substitution gain`: differential avoided-emissions proxy for material use versus direct energy use,
- `Supply-chain savings`: differences in simplified material and bioenergy supply-chain emission factors.

The forest carbon opportunity-cost term is country-specific rather than fixed. It increases where observed harvest intensity and forest carbon stock density are relatively high, which keeps the carbon effect tied to land-use context rather than a single generic coefficient.

To avoid presenting a single deterministic answer as if it were settled truth, the model also runs a 400-draw sensitivity analysis across the main carbon-accounting and scenario-intensity assumptions. This produces EU-level uncertainty ranges and country-level robustness shares.

The subnational extension is intentionally conservative in what it claims. The project does not claim to observe forestry production directly at NUTS-2 level. Instead, it downscales country-level scenario value to NUTS-2 regions in proportion to each region’s share of national woodland area, creating an explicitly labeled regional screening layer.

The agricultural side of the project is still simplified, but it was strengthened in the latest iteration. The `Food-Land Safeguard` is no longer based only on land-cover shares. It now also uses a country-level `food_production_intensity_index` built from official Eurostat crop statistics for cereals, pulses, potatoes, and vegetables. That index enters the food-land proxy alongside cropland, grassland, feed-land, and permanent-crop context.

The metric basis is now made explicit in the outputs. The Sweden empirical rerun is a `forest-only` comparison and ranks forest scenarios in `EUR/forest ha`. The integrated and optimized NUTS-2 layers compare forest and food-land policies together and therefore rank options in `EUR/ha of total land`. This distinction matters in southern Sweden: `SE22` keeps `Material Cascade` as its best forest policy, but `Food-Land Safeguard` is slightly stronger in the broader integrated land-use screen.

The final step adds a small constrained allocation model. For each NUTS-2 region, the model chooses exactly one option from the set of forest and food-land policies. The objective is to maximize total policy value under a carbon price of `EUR 100/tCO2`, subject to two Europe-wide safeguards:

- retain at least `97%` of baseline regionalized biomass supply,
- safeguard at least `22%` of the available crop-capacity proxy.

This is still a screening model rather than a full sector-equilibrium or integrated assessment framework, but it moves the project closer to the style of biophysical-economic land-use modeling described in the Chalmers job advertisement.

## Main Findings

At EU country level, the project finds that both `Material Cascade` and `Conservation Priority` outperform `Bioenergy Push` under the default parameterization:

- `Material Cascade`: about `18.4 MtCO2e` net climate benefit relative to baseline,
- `Conservation Priority`: about `17.1 MtCO2e`,
- `Bioenergy Push`: about `-21.8 MtCO2e`.

The sensitivity analysis shows that this conclusion is structurally robust in one important respect: `Bioenergy Push` never becomes the best EU-wide option across the 400 parameter draws. `Material Cascade` is the best EU-wide option in about `56%` of runs and `Conservation Priority` in about `44%`. This matters because it shows the project is not just producing point estimates, but also separating stable from assumption-sensitive conclusions.

At NUTS-2 level, the unconstrained integrated screen selects:

- `Material Cascade` in `92` regions,
- `Conservation Priority` in `79`,
- `Food-Land Safeguard` in `40`,
- `Bioenergy Push` in `0`.

The constrained portfolio changes that pattern in a revealing way. Once the model is required to preserve biomass supply and protect food-related capacity at EU scale, the selected portfolio becomes:

- `Material Cascade` in `123` regions,
- `Conservation Priority` in `34`,
- `Food-Land Safeguard` in `54`,
- `Bioenergy Push` in `0`.

In total, `45` NUTS-2 regions switch away from their unconstrained locally best option once those Europe-wide constraints are enforced. The optimized portfolio retains about `97.0%` of baseline regionalized biomass supply and safeguards about `45.6%` of the available crop-capacity proxy, comfortably above the minimum `22%` threshold. At `EUR 100/tCO2`, the resulting portfolio value is about `EUR 2.15 billion`.

## Why This Demonstrates Fit

The value of this project for the application is not that it is a complete research model. It is that it demonstrates the right kind of early research behavior.

First, it shows `land-use and biomass systems thinking`. The project links forest carbon storage, biomass extraction, material use, direct energy use, agricultural land competition, and regional policy choices in one coherent workflow.

Second, it shows `carbon-accounting competence`. The model distinguishes between forest carbon retention, substitution effects, and supply-chain emissions instead of flattening everything into a generic climate score.

Third, it shows `spatial data capability`. The workflow handles official European geometry and regional land-cover data, constructs NUTS-2 outputs, and generates interpretable figures and tables.

Fourth, it shows `policy-relevant trade-off analysis`. The constrained portfolio is especially important here, because it forces the project to make explicit trade-offs between climate value, biomass supply, and food-related land capacity rather than merely ranking regions one by one.

Fifth, it shows `methodological honesty`. The repository is explicit about what is directly observed, what is proxy-based, and what a fuller research model would still need to improve.

## Limits

The project remains intentionally smaller than a doctoral research model. It does not include dynamic forest growth and age classes, direct regional forestry production data, direct agricultural greenhouse gas inventories, market equilibrium effects, leakage, or richer biodiversity constraints. The NUTS-2 forestry results remain a screening extension derived from country-level results rather than direct regional forestry accounting. The agricultural side is improved but still proxy-based. Those limitations are important and are stated clearly throughout the repository.

## How This Could Extend Into PhD Work

The most credible next PhD-stage extensions would be:

- replacing woodland-share downscaling with better regional forestry observations,
- replacing country-level crop-intensity transfer with direct regional agricultural production or GHG indicators,
- adding biodiversity or protected-area constraints,
- calibrating opportunity-cost and substitution assumptions more tightly to literature,
- extending the constrained portfolio into a richer biophysical-economic model with stronger sector coupling.

## Bottom Line

This project now functions as a strong application artifact because it is easy to understand, methodologically honest, and directly targeted to the scientific profile of the Chalmers position. It shows not only the ability to code and analyze data, but also the ability to frame a land-use and climate problem in a way that is recognizably relevant to doctoral research.
