# EU Forest Biomass Trade-off Explorer

A reproducible EU land-use and biomass trade-off project combining country-level forest scenario analysis, sensitivity-based robustness testing, official crop-production context, a NUTS-2 land-competition screen, and a Sweden empirical sub-study that replaces woodland-share downscaling with official subnational forest area, biomass, and increment data.

For academic applications, the best way to read this repository is as a transparent research-style prototype: strong enough to demonstrate quantitative modeling, spatial data handling, and land-use systems reasoning, but intentionally honest about its limits as a screening and decision-support model rather than a finished sector framework.

## Research Question

How do different forest biomass allocation strategies across EU countries change the balance between forest carbon retention, harvested biomass use, and policy-relevant climate value, and where do those forest options begin to conflict with agricultural land that is important for food and feed?

This project focuses on three policy-relevant alternatives:

- `Conservation Priority`: reduce total harvest by 15 percent, drawing the cut from wood fuel first.
- `Material Cascade`: keep harvest constant, but reallocate 20 percent of wood fuel to industrial roundwood uses.
- `Bioenergy Push`: increase total harvest by 15 percent and allocate the extra harvest to direct energy use.

## Why This Is Relevant

The Chalmers PhD combines land-use systems analysis, climate impact modeling, and economic reasoning. This repository is designed as a smaller but defensible version of that style of work:

- it uses real official spatial and statistical data,
- it treats land-use carbon and biomass allocation as linked problems,
- it compares scenarios rather than describing a single status quo,
- it adds a light economic framing through carbon value per hectare at a stated carbon price,
- it is explicit about what is measured directly and what is represented by proxy assumptions.

## Data Sources

- FAOSTAT Land Use bulk download: forest area, living biomass carbon stock, naturally regenerating forest area, planted forest area, primary forest area.
- FAOSTAT Forestry bulk download: roundwood, industrial roundwood, wood fuel, sawnwood, and wood pellet production.
- Eurostat GISCO country polygons: EU-27 country geometries for mapping.
- Eurostat GISCO NUTS-2 polygons: subnational geometry for the regional screening layer.
- Eurostat `lan_lcv_ovw`: regional land-cover statistics used to measure NUTS-2 woodland, cropland, grassland, fodder, and permanent-crop context.
- Eurostat `apro_cpsh1`: country-level crop area, production, and yield statistics for cereals, pulses, potatoes, and vegetables, used to build a simple food-production-intensity profile.
- Swedish University of Agricultural Sciences (SLU) PxWeb tables from the Swedish National Forest Inventory:
  - Table 3.1a productive forest area by county, `2022` five-year average.
  - Table 3.29b tree dry weight biomass by county, `2022` five-year average.
  - Table 3.31a mean annual volume increment by county, `2019` average year.

All raw data sources are downloaded through the pipeline into [`data/raw`](data/raw).

## Method Summary

The model works at EU country level for the latest year shared across the official datasets, which is 2024.

Baseline indicators are derived from observed data:

- forest area and forest carbon stock,
- harvest intensity in cubic meters per hectare,
- wood fuel share in total roundwood harvest,
- a simple material recovery ratio using sawnwood over industrial roundwood,
- a biodiversity-pressure proxy based on harvest intensity multiplied by the share of naturally regenerating forest.

Scenario results are then evaluated with three climate-accounting components:

- `forest carbon retention`: avoided forest carbon opportunity cost when harvest falls relative to baseline,
- `substitution gain`: the incremental benefit of moving wood into material use versus direct energy use,
- `supply-chain savings`: differences in simplified harvest and processing emissions proxies.

The country-specific forest carbon opportunity cost factor is higher where observed harvest intensity and carbon stock density are higher. This keeps the scenario model tied to real land-use conditions instead of using a single EU-wide coefficient.

To make the conclusions more research-ready, the pipeline also runs a fixed-seed sensitivity analysis over `400` parameter draws. That robustness layer varies:

- forest carbon opportunity-cost assumptions,
- substitution and supply-chain coefficients,
- the size of harvest reduction, harvest increase, and wood-fuel-to-material shifts.

This allows the project to distinguish between `stable` country recommendations and `assumption-sensitive` ones.

The project now includes four linked regional extensions. The first uses official Eurostat regional woodland area and composition to downscale country-level forest results into a NUTS-2 screening layer. The second adds an integrated policy screen that compares those forest options with a `Food-Land Safeguard` option derived from observed cropland and grassland shares plus a transparent displacement-risk proxy for marginal agricultural land. That food-land term now also uses an official Eurostat crop-production-intensity index at country level, so the agricultural side is no longer based only on land-cover shares. The third extension solves a constrained regional portfolio problem: select one policy per NUTS-2 region to maximize total climate value while retaining at least `97%` of baseline regionalized biomass supply and safeguarding at least `22%` of available crop-capacity proxy. The fourth extension is a Sweden empirical sub-study that aggregates official county-level SLU forest area, dry biomass, and annual increment to Swedish NUTS-2 regions, then reruns the forest scenario model region by region using real subnational forest stocks and increment-based harvest allocation rather than pure woodland-share downscaling.

Full details are documented in [`docs/methods_note.md`](docs/methods_note.md), [`docs/assumptions.md`](docs/assumptions.md), and [`docs/limitations.md`](docs/limitations.md).

## Main Outputs

Running the pipeline creates:

- a best-scenario choropleth map: [`figures/best_scenario_map.png`](figures/best_scenario_map.png)
- an EU-level scenario decomposition chart: [`figures/eu_scenario_decomposition.png`](figures/eu_scenario_decomposition.png)
- a country-level trade-off scatterplot: [`figures/country_tradeoff_scatter.png`](figures/country_tradeoff_scatter.png)
- an EU uncertainty-range figure from 400 sensitivity runs: [`figures/eu_uncertainty_ranges.png`](figures/eu_uncertainty_ranges.png)
- a country robustness heatmap: [`figures/country_robustness_heatmap.png`](figures/country_robustness_heatmap.png)
- a modal best-scenario robustness map: [`figures/robust_best_scenario_map.png`](figures/robust_best_scenario_map.png)
- a NUTS-2 regional screening map: [`figures/nuts2_priority_map.png`](figures/nuts2_priority_map.png)
- a NUTS-2 woodland context scatterplot: [`figures/nuts2_context_scatter.png`](figures/nuts2_context_scatter.png)
- an integrated NUTS-2 policy-priority map: [`figures/nuts2_integrated_policy_map.png`](figures/nuts2_integrated_policy_map.png)
- a forest-versus-food regional trade-off scatterplot: [`figures/nuts2_forest_food_tradeoff.png`](figures/nuts2_forest_food_tradeoff.png)
- an integrated NUTS-2 policy summary chart: [`figures/nuts2_integrated_policy_summary.png`](figures/nuts2_integrated_policy_summary.png)
- a constrained NUTS-2 policy portfolio map: [`figures/nuts2_optimized_policy_map.png`](figures/nuts2_optimized_policy_map.png)
- a constrained portfolio summary figure: [`figures/nuts2_optimized_portfolio_summary.png`](figures/nuts2_optimized_portfolio_summary.png)
- a Sweden empirical NUTS-2 map using official SLU data: [`figures/sweden_nuts2_empirical_best_scenario_map.png`](figures/sweden_nuts2_empirical_best_scenario_map.png)
- a Sweden comparison chart showing how the empirical layer differs from woodland-share downscaling: [`figures/sweden_nuts2_empirical_comparison.png`](figures/sweden_nuts2_empirical_comparison.png)
- country-by-scenario results: [`outputs/scenario_results_by_country.csv`](outputs/scenario_results_by_country.csv)
- EU aggregate scenario summary: [`outputs/scenario_summary_eu.csv`](outputs/scenario_summary_eu.csv)
- a ranking table based on carbon value per hectare: [`outputs/country_ranking_table.csv`](outputs/country_ranking_table.csv)
- sensitivity parameter draws: [`outputs/sensitivity_parameter_draws.csv`](outputs/sensitivity_parameter_draws.csv)
- EU uncertainty summary: [`outputs/sensitivity_eu_uncertainty_summary.csv`](outputs/sensitivity_eu_uncertainty_summary.csv)
- country robustness summary: [`outputs/sensitivity_country_modal_scenario.csv`](outputs/sensitivity_country_modal_scenario.csv)
- NUTS-2 screening table: [`outputs/nuts2_top_regions_table.csv`](outputs/nuts2_top_regions_table.csv)
- integrated NUTS-2 policy priorities: [`outputs/nuts2_integrated_policy_priorities.csv`](outputs/nuts2_integrated_policy_priorities.csv)
- regions that switch from a forest-only recommendation to a food-land safeguard: [`outputs/nuts2_policy_switch_regions.csv`](outputs/nuts2_policy_switch_regions.csv)
- optimized regional portfolio: [`outputs/nuts2_optimized_policy_portfolio.csv`](outputs/nuts2_optimized_policy_portfolio.csv)
- optimized policy summary: [`outputs/nuts2_optimized_policy_summary.csv`](outputs/nuts2_optimized_policy_summary.csv)
- optimized constraint summary: [`outputs/nuts2_optimized_constraint_summary.csv`](outputs/nuts2_optimized_constraint_summary.csv)
- Sweden empirical baseline metrics: [`data/processed/sweden_nuts2_empirical_baseline_metrics.csv`](data/processed/sweden_nuts2_empirical_baseline_metrics.csv)
- Sweden empirical scenario results: [`outputs/sweden_nuts2_empirical_scenario_results.csv`](outputs/sweden_nuts2_empirical_scenario_results.csv)
- Sweden empirical-versus-screening comparison: [`outputs/sweden_nuts2_screening_comparison.csv`](outputs/sweden_nuts2_screening_comparison.csv)
- run manifest with datasets, parameters, timestamp, and Git hash when available: [`outputs/run_manifest.json`](outputs/run_manifest.json)
- consistency audit explaining the Sweden-versus-integrated SE22 case and current structural warnings: [`outputs/consistency_audit.md`](outputs/consistency_audit.md)

## Metric Guide

The repository now exposes the metric basis explicitly because different layers answer different questions:

- country and Sweden empirical forest reruns use `value_eur_per_forest_ha` for forest-only scenario ranking,
- integrated and optimized NUTS-2 policy outputs use `value_eur_per_land_ha` because they compare forest options against a food-land policy over total regional land area,
- output tables also carry `is_forest_only` and `includes_food_policy` so the policy space is visible in the data rather than inferred from figure titles.

This matters for interpretation. A region can keep `Material Cascade` as its best forest policy while still selecting `Food-Land Safeguard` in the integrated screen if the food-land option is slightly stronger on a total-land basis.

## Headline Findings

With the default parameterization and a carbon price of EUR 100/tCO2:

- `Material Cascade` yields the strongest EU-wide climate benefit relative to baseline at about `18.4 MtCO2e`.
- `Conservation Priority` is close behind at about `17.1 MtCO2e`.
- `Bioenergy Push` is strongly negative at about `-21.8 MtCO2e`.
- `Material Cascade` is the best-performing scenario in 15 EU countries.
- `Conservation Priority` is the best-performing scenario in 12 EU countries.

That split is useful for portfolio purposes because it shows the model is not hard-coded to make one answer win everywhere. Countries with higher observed harvest pressure and denser forest carbon stocks tend to lean more toward conservation, while countries with larger direct energy-wood shares often gain from shifting existing harvest toward material uses.

With the new sensitivity layer:

- `Material Cascade` is the best EU-wide scenario in about `56%` of parameter draws.
- `Conservation Priority` is best EU-wide in about `44%` of draws.
- `Bioenergy Push` never becomes the best EU-wide scenario.
- Some countries are highly robust, while others are clearly assumption-sensitive.
  Belgium and Czechia are very stable toward conservation.
  Cyprus, Greece, and Italy are very stable toward material cascade.
  Spain, Romania, Lithuania, Portugal, and Finland are more borderline.

With the NUTS-2 screening extension:

- the project now identifies where country-level scenario value is most concentrated in regional woodland landscapes,
- top screening regions include forest-relevant parts of France, Germany, and Estonia,
- the subnational layer is explicitly labeled as a downscaled screening product rather than a direct regional production model.

With the Sweden empirical sub-study:

- official county-level SLU forest area, dry biomass, and annual increment are aggregated to all `8` Swedish NUTS-2 regions,
- the empirical Sweden forest-only scenario rerun selects `Material Cascade` in all `8` Swedish NUTS-2 regions under the default parameterization,
- relative to the original woodland-share screening, the empirical Sweden layer lowers the estimated best-scenario land value in `SE12`, `SE21`, and especially `SE22`, but raises it in `SE31`, `SE32`, and `SE33`,
- the strongest downward revision appears in `SE22 Sydsverige`, where the screening layer suggested about `EUR 8.6/ha` of total land but the empirical SLU-based layer gives about `EUR 1.6/ha`,
- the strongest upward revisions appear in northern Sweden, where `SE32` and `SE33` rise to roughly `EUR 11.3/ha` and `EUR 12.2/ha` of total land,
- a direct side-by-side comparison is available for `6` Swedish NUTS-2 regions; `SE11` and `SE23` are still absent from the selected Eurostat land-cover comparison layer even though the empirical Sweden map covers all `8`,
- the apparent `SE22` discrepancy is valid model behavior: the forest-only Sweden map ranks forest policies in `EUR/forest ha`, while the integrated screen compares forest plus food-land options in `EUR/ha of total land`, and the food-land safeguard is slightly higher there.

With the integrated forest-versus-food screen:

- `Material Cascade` remains the selected priority in `92` NUTS-2 regions,
- `Conservation Priority` is selected in `79` NUTS-2 regions,
- `Food-Land Safeguard` is selected in `40` NUTS-2 regions once agricultural land competition is made explicit,
- `Bioenergy Push` is not selected in any NUTS-2 region,
- food-land safeguard regions are concentrated in places with high agricultural shares and relatively weak forest-option value, including Malta, Cyprus, parts of France, Greece, Spain, Belgium, and the western Netherlands.

With the constrained regional portfolio:

- the model selects `123` NUTS-2 regions for `Material Cascade`,
- `34` for `Conservation Priority`,
- `54` for `Food-Land Safeguard`,
- `0` for `Bioenergy Push`,
- `45` regions switch away from their unconstrained best option once biomass-supply and food-capacity safeguards are enforced,
- the optimized portfolio retains about `97.0%` of baseline regionalized biomass supply while safeguarding about `45.6%` of available crop-capacity proxy,
- the optimized portfolio value is about `EUR 2.15 billion` at `EUR 100/tCO2`.

## Policy and Decision-Support Relevance

This is still not a full forest-sector or land-system optimization model, but it now supports a more explicit policy-style decision frame:

- it identifies which countries are more likely to benefit from conservation-oriented versus cascade-oriented strategies,
- it translates climate benefit into `EUR/ha` under an explicit carbon-price assumption,
- it extends that logic to subnational regions by comparing forest options with a food-land safeguard proxy informed by official crop-production intensity,
- it selects an EU-wide regional policy mix under explicit biomass-supply and food-capacity safeguards,
- it makes trade-offs visible rather than hiding them in a single composite score.

The intended use is screening and communication, not regulatory decision-making.

## Reproducibility

Create a virtual environment, install dependencies, and run the pipeline:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
PYTHONPATH=src python -m eu_forest_biomass_tradeoff_explorer.pipeline
pytest
```

The pipeline will download missing raw data automatically, then rebuild processed data, baseline figures, sensitivity outputs, and tables.
It also writes a machine-readable run manifest and a consistency audit to `outputs/`.

## GitHub Publishing Note

For a public GitHub version of this project:

- downloaded raw datasets under `data/raw/` are ignored and should be regenerated through the pipeline,
- figures and selected outputs are kept as portfolio artifacts so the repository is readable without rerunning everything first,
- cache and packaging by-products such as `__pycache__`, `.pytest_cache`, and `*.egg-info` should not be committed.

## Repository Structure

```text
eu-forest-biomass-tradeoff-explorer/
  README.md
  pyproject.toml
  data/
    raw/
    processed/
  docs/
    assumptions.md
    chalmers_research_note.md
    limitations.md
    methods_note.md
    parameter_grounding_note.md
    portfolio_translation.md
    short_research_report.md
    self_audit.md
  figures/
  notebooks/
  outputs/
  src/
    eu_forest_biomass_tradeoff_explorer/
  tests/
```

## Limitations

- The core forest scenario model still works at country level rather than at NUTS-2 production level or stand level.
- Most NUTS-2 layers remain screening extensions based on regional land cover and downscaled country forest results, although the Sweden case study now replaces that downscaling with official county-level forest area, biomass, and increment data aggregated to NUTS-2.
- The carbon accounting is deliberately simplified and uses transparent proxy coefficients for substitution and supply-chain emissions.
- Forest carbon dynamics are represented as an opportunity-cost framing, not a dynamic age-class forest model.
- Biodiversity is represented with a pressure proxy, not ecological survey data or habitat modeling.
- The new food-land safeguard is stronger than before because it now uses official Eurostat crop-production intensity, but it is still not a direct regional agricultural GHG inventory.
- The Sweden empirical case still allocates harvested biomass product mix from Sweden's national FAOSTAT wood-use profile and converts dry biomass to carbon with a fixed `0.50 tC/t dry biomass` factor.
- The constrained portfolio is explicit, but it is still a small linear screening model rather than a calibrated sector-coupling or market-equilibrium model.
- The sensitivity layer tests structural robustness, but it is still a parameter sweep rather than a formal probabilistic calibration to literature-based distributions.

Those constraints are deliberate. The goal is a credible proof-of-capability project that is transparent about scope rather than an overclaimed pseudo-IAM.

## Portfolio Translation

CV bullets, a GitHub description, and a short application-facing narrative are in [`docs/portfolio_translation.md`](docs/portfolio_translation.md).

A skeptical role-fit review is in [`docs/self_audit.md`](docs/self_audit.md).

The literature-grounding note is in [`docs/parameter_grounding_note.md`](docs/parameter_grounding_note.md), and the short paper-style synthesis is in [`docs/short_research_report.md`](docs/short_research_report.md).

A Chalmers-specific alignment note is in [`docs/chalmers_research_note.md`](docs/chalmers_research_note.md).

The application-facing package is in:

- [`docs/chalmers_application_brief.pdf`](docs/chalmers_application_brief.pdf)
- [`docs/chalmers_application_brief.md`](docs/chalmers_application_brief.md)
- [`docs/chalmers_personal_letter_draft.md`](docs/chalmers_personal_letter_draft.md)
- [`docs/chalmers_figure_selection.md`](docs/chalmers_figure_selection.md)
- [`docs/chalmers_cv_version.md`](docs/chalmers_cv_version.md)

To rebuild the PDF brief:

```bash
python -m eu_forest_biomass_tradeoff_explorer.application_brief
```
