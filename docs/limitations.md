# Limitations

## Structural Limits

- The model works at country level, so it cannot represent within-country heterogeneity in forest type, yield, age structure, or management intensity.
- The analysis is cross-sectional for 2024 rather than dynamic over time.
- Trade flows are not endogenized, so the model cannot estimate leakage or imported biomass substitution.
- Most NUTS-2 extensions are still downscaled screening layers, not direct regional forest production or agricultural emissions databases.
- The new Sweden empirical case improves that weak point for one subset by using official county-level forest area, biomass, and increment aggregated to NUTS-2, but it does not yet generalize that empirical treatment across Europe.

## Carbon Accounting Limits

- The forest carbon effect is represented as a country-adjusted opportunity-cost proxy rather than a dynamic forest growth and decay model.
- Substitution and supply-chain factors are stylized coefficients meant for transparent comparison, not for national inventory use.
- The model does not track harvested wood product pools, decay, methane, albedo, or time-resolved biogenic carbon dynamics.
- In the Sweden empirical sub-study, dry biomass is converted to carbon with a fixed `0.50 tC/t dry biomass` factor rather than species- or pool-specific carbon fractions.

## Land-Use and Ecology Limits

- Biodiversity is represented through a pressure proxy only.
- Primary forest area is included as contextual information but not used directly in the core scenario score because country coverage is incomplete.
- The project does not include explicit conservation targets, protected-area constraints, or habitat suitability layers.
- The food-land safeguard is stronger than a pure land-cover proxy because it now uses official crop-production intensity at country level, but it still does not model regional crop yields, livestock systems, or agricultural greenhouse gas inventories directly.
- Two Swedish NUTS-2 regions, `SE11` and `SE23`, are covered in the empirical forest case study but are still absent from the direct empirical-versus-screening comparison because the selected Eurostat land-cover extract does not provide usable matching values there.

## Economic Limits

- The economic component is limited to carbon value per hectare plus a small constrained allocation model under a stated carbon price.
- The new optimization is deliberately simple: one option per region, one biomass floor, and one food-capacity floor.
- There is still no observed cost curve, market equilibrium model, or endogenous commodity-price feedback for harvest reduction, biomass reallocation, or agricultural land diversion.
- Private profitability, public budgets, and commodity prices are not modeled directly.
- The Sweden empirical case improves regional biophysical realism, but it still applies Sweden's national harvested-wood product mix to all Swedish regions rather than observing regional product use directly.

## Uncertainty Limits

- The sensitivity analysis improves robustness assessment, but it is still an exploratory parameter sweep rather than a fully calibrated uncertainty model.
- The parameter ranges are transparent stress-test bands, not posterior distributions estimated from primary literature or empirical calibration.
- Interaction effects are sampled across broad ranges, but the workflow does not yet provide variance decomposition, Bayesian updating, or formal global sensitivity indices.

## Why These Limits Are Acceptable Here

This repository is a proof-of-capability project, not a production policy model.

What it is meant to demonstrate:

- the ability to define a system boundary,
- responsible use of official data,
- carbon-accounting logic,
- spatial data handling,
- scenario-based trade-off reasoning,
- a small explicit allocation / optimization step,
- transparent communication of uncertainty.

What a fuller research model would improve:

- dynamic forest growth and age classes,
- multi-period scenario pathways,
- explicit agricultural production and GHG accounting,
- empirical subnational forestry datasets beyond Sweden,
- direct regional crop-yield or livestock indicators instead of country-level crop-intensity transfer,
- better ecological indicators,
- explicit trade and market feedbacks,
- sector coupling with food and energy systems,
- calibrated uncertainty analysis and formal sensitivity decomposition.

Being explicit about those gaps is part of the point.
