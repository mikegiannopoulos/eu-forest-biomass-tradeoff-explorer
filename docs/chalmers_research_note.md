# Chalmers Research Note

## Purpose

This note explains how the repository aligns with the Chalmers doctoral position `Doctoral student in Land Use and Climate Impacts` and why the project is a credible portfolio-scale precursor to that kind of work.

## Why This Project Matches The Position

The official ad emphasizes four things in particular:

1. biophysical and economic modeling of greenhouse gas emissions from forest and agricultural systems,
2. trade-offs between carbon sequestration, wood use, food production, energy, and conservation,
3. analysis at European and sub-national levels,
4. quantitative scientific computing with spatial data.

This repository now addresses each of those directly:

- `Biophysical modeling`
  The core scenario model combines forest carbon opportunity cost, substitution effects, and supply-chain emissions proxies for EU forestry systems.

- `Economic modeling`
  The project values policy outcomes under an explicit carbon price and now adds a constrained regional allocation step that selects one NUTS-2 policy per region under biomass-supply and food-capacity safeguards.

- `Forest and agriculture`
  The forest side is built from FAOSTAT land-use and forestry data. The agricultural side is still simplified, but it now uses official Eurostat crop-production statistics plus NUTS-2 cropland and grassland context instead of relying only on land-cover shares.

- `European and sub-national analysis`
  The workflow operates at EU country level and extends to NUTS-2 regions through Eurostat GISCO geometry and Eurostat regional land-cover statistics.

- `Spatial and computational capability`
  The project is implemented in reproducible Python code, generates maps and tables, and includes tests, methods documentation, assumptions, limitations, and a short report.

## What The Project Does Not Claim

This repository does **not** claim to reproduce the ClimAg or CRAFT models, and it does **not** claim to be a TERRAMARE tool.

Instead, it should be read as a transparent screening and decision-support prototype that demonstrates:

- relevant systems framing,
- credible carbon-accounting logic,
- spatial data competence,
- early biophysical-economic modeling instincts,
- honest handling of uncertainty and scope limits.

That honesty matters because overclaiming would weaken, not strengthen, the application.

## Why The New Optimization Layer Matters

Before the latest extension, the repository mainly asked: `Which option looks best in each country or region?`

Now it can also ask: `Which EU-wide regional mix should be chosen if policymakers want to keep biomass supply high while still protecting food-related land capacity?`

That is closer to the PhD ad because it introduces a real allocation problem:

- one policy per NUTS-2 region,
- maximize total climate value,
- maintain at least `97%` of baseline regionalized biomass supply,
- safeguard at least `22%` of available crop-capacity proxy.

This is still a small model, but it is much closer to the logic of land-use policy analysis than a static dashboard or unconstrained ranking exercise.

## Why The Agricultural Extension Matters

The ad explicitly states that the research may also explore the climate and environmental footprint of agriculture and food.

The repository still does not contain a full agricultural GHG model, but it now makes a better first step by using:

- NUTS-2 cropland, grassland, fodder, and permanent-crop shares from Eurostat,
- country-level crop area, production, and yield from Eurostat `apro_cpsh1`,
- a transparent food-production-intensity index for the food-land safeguard.

This makes the project much more obviously relevant to the `wood, food, energy, and conservation` framing in the ad.

## How This Could Extend Into Actual Doctoral Work

A realistic first-year PhD extension from this repository would be:

- replacing downscaled regional forest quantities with better subnational forestry data,
- replacing crop-intensity transfer with direct regional agricultural production or GHG indicators,
- introducing better biodiversity or protected-area constraints,
- calibrating substitution and carbon-opportunity assumptions more tightly to literature,
- extending the constrained portfolio into a richer biophysical-economic model.

That path is credible because the current repo already has the right structure: data ingestion, harmonization, scenario accounting, spatial joins, sensitivity analysis, constrained allocation, and documentation.

## Bottom Line

As a portfolio artifact, this project now signals more than generic climate interest. It shows that the applicant can already work in the style the Chalmers position calls for: integrating forestry and food-land trade-offs, handling European spatial data, building transparent climate-accounting logic, and translating that into policy-relevant regional allocation analysis without overstating what the model can do.

## Recommended Application Framing

The strongest way to frame this repository in the application is:

`This project demonstrates that I can formulate a Chalmers-relevant land-use research question, assemble official European datasets, build a reproducible quantitative workflow in Python, and make trade-offs between forest carbon, harvested wood use, food-land pressure, and regional policy constraints explicit.`

That framing works because it is ambitious enough to be impressive but restrained enough to stay credible.
