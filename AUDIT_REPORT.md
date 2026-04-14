# Audit Report

## Project overview

This project is a research-style Python package that builds an EU forest biomass trade-off workflow from official data sources, then extends the analysis with NUTS-2 screening, a stylized food-land safeguard, a constrained regional portfolio optimization, and a Sweden empirical sub-study using SLU county data.

At a high level, the implementation is more serious and reproducible than a notebook-only portfolio project:

- core logic lives in importable modules under `src/eu_forest_biomass_tradeoff_explorer/`
- the main workflow is scriptable through `python -m eu_forest_biomass_tradeoff_explorer.pipeline`
- the codebase is separated into data loading, model logic, sensitivity, regionalization, optimization, plotting, and presentation
- the repository includes raw, processed, and derived outputs plus method notes and explicit limitations

However, the audit also found several real upgrade targets:

- one country with zero observed harvest still receives a misleading “best scenario” and “100% robust” recommendation
- NUTS-2 coverage is silently incomplete because the project inner-joins 2024 geometry with a land-cover table that does not align cleanly by region code
- several Eurostat missing-data and quality-flag issues are currently flattened into numeric zeros
- narrative docs are already drifting from regenerated outputs
- result files are reproducible on the current machine, but there is no run manifest tying outputs to exact raw-data snapshots, parameter values, or code state

This should be treated as a credible screening model with strong engineering instincts, not yet as a publication-ready evidence product.

## Repository map

### Main entrypoints

- `src/eu_forest_biomass_tradeoff_explorer/pipeline.py`
  Orchestrates the full workflow from raw-data access through outputs and figures.
- `src/eu_forest_biomass_tradeoff_explorer/application_brief.py`
  Builds the Chalmers application PDF from generated figures.
- `pyproject.toml`
  Defines packaging and console scripts:
  `run-eu-forest-biomass-tradeoffs`
  `build-chalmers-application-brief`

### Source modules

- `data.py`: raw download, FAOSTAT loading, Eurostat crop profile, country geometry loading
- `model.py`: baseline metrics, scenario logic, scenario evaluation, ranking
- `sensitivity.py`: fixed-seed parameter sampling and robustness outputs
- `regional.py`: NUTS-2 land-cover loading, downscaling, Sweden comparison layer
- `allocation.py`: integrated forest-versus-food option construction and unconstrained regional policy selection
- `optimization.py`: MILP-based constrained regional portfolio
- `plotting.py`: all figure generation
- `sweden.py`: SLU API download, county parsing, Swedish empirical NUTS-2 case study
- `config.py`: all central constants and default parameters

### Tests

- `tests/test_model.py`
  Only test file in the repo. It covers scenario logic, sensitivity distributions, screening allocation, integrated policy switching, optimization constraints, and some plotting helper logic.

### Data and outputs

- `data/raw/`
  Official source downloads and API responses.
- `data/processed/`
  Processed country metrics, screening tables, and GeoJSON map layers.
- `outputs/`
  Scenario tables, sensitivity outputs, integrated policy results, optimization results, and Sweden comparisons.
- `figures/`
  Final PNG figures plus `FIGURE_QA_REPORT.md`.

### Docs

- Core project docs:
  `docs/methods_note.md`
  `docs/assumptions.md`
  `docs/limitations.md`
  `docs/parameter_grounding_note.md`
  `docs/short_research_report.md`
  `docs/self_audit.md`
  `docs/portfolio_translation.md`
- Application-facing material mixed into the same docs folder:
  `docs/chalmers_*`

### Environment and build artifacts present in the local directory

- `.venv/`
- `.pytest_cache/`
- `src/eu_forest_biomass_tradeoff_explorer.egg-info/`
- `src/eu_forest_biomass_tradeoff_explorer/__pycache__/`
- `tests/__pycache__/`

These are ignored by `.gitignore`, but they are present in this working directory and make the project presentation noisier than it needs to be.

### Git state

This directory is not currently inside a Git repository. Commit history, branch context, and historical provenance could not be verified from the local checkout.

## Workflow reconstruction

### Reconstructed workflow

`data/raw` -> preprocessing in `data.py` and `sweden.py` -> baseline country metrics in `model.py` -> deterministic scenario outputs -> sensitivity analysis -> NUTS-2 screening -> integrated forest-vs-food option set -> constrained optimization -> CSV/GeoJSON outputs -> figures -> optional Chalmers PDF brief

### Concrete execution path

1. `pipeline.main()` ensures directories and downloads missing raw data.
2. `build_baseline_inputs()` loads:
   - FAOSTAT land use
   - FAOSTAT forestry
   - Eurostat crop-production profile
3. `build_baseline_metrics()` computes forest area, carbon stock density, harvest intensity, wood-fuel share, biodiversity proxy, and country-specific forest carbon opportunity cost.
4. `evaluate_scenarios()` evaluates baseline plus three alternative scenarios.
5. `summarize_scenarios()`, `ranking_table()`, and `best_scenario_by_country()` generate country outputs.
6. `run_sensitivity_analysis()` runs 400 fixed-seed draws over proxy parameters.
7. `build_nuts2_screening_dataset()` merges 2024 NUTS-2 geometry with Eurostat land-cover context and downscales country results by woodland share.
8. `build_sweden_empirical_nuts2_case_study()` builds an empirical Swedish sub-study from SLU county data aggregated to NUTS-2.
9. `compare_sweden_empirical_to_screening()` compares the empirical Swedish layer with the woodland-share screen.
10. `build_regional_policy_options()` creates regional forest options plus a `Food-Land Safeguard`.
11. `select_regional_policy_priorities()` selects the best unconstrained option per region.
12. `optimize_regional_policy_portfolio()` solves the constrained EU-wide regional portfolio.
13. `_write_outputs()` overwrites all CSV, GeoJSON, and PNG artifacts in fixed locations.
14. `application_brief.py` reads generated figures and builds a PDF.

## Strengths

### What looks solid

- The project uses actual source data rather than fabricated CSVs or notebook constants.
- Evidence:
  `config.py` defines concrete raw datasets and URLs for FAOSTAT, Eurostat GISCO, Eurostat JSON-stat, and SLU API-backed files.
- Why it increases trust:
  This creates a real provenance chain from official data to derived outputs.
- Remaining caveat, if any:
  Provenance exists in code and raw files, but not yet in a dedicated manifest.

### What looks solid

- Core analytical logic is modular and script-driven rather than notebook-bound.
- Evidence:
  `pipeline.py`, `data.py`, `model.py`, `regional.py`, `allocation.py`, `optimization.py`, and `plotting.py` split responsibilities cleanly.
  The only notebook, `notebooks/01_country_tradeoffs.ipynb`, is a thin reader over already-generated outputs.
- Why it increases trust:
  This reduces hidden notebook state and makes regeneration realistic.
- Remaining caveat, if any:
  The main pipeline is still monolithic at runtime and not parameterized from a run config.

### What looks solid

- The project is transparent about methodological scope and limitations.
- Evidence:
  `docs/methods_note.md`, `docs/assumptions.md`, `docs/limitations.md`, and `docs/parameter_grounding_note.md` explicitly describe proxy structure, scope boundaries, and what is not modeled.
- Why it increases trust:
  The code is not pretending to be a dynamic forest-sector or equilibrium land-use model.
- Remaining caveat, if any:
  Some narrative docs still overstate stability because they are not generated from live outputs.

### What looks solid

- Deterministic robustness logic is present and reproducible.
- Evidence:
  `sensitivity.py` uses `np.random.default_rng(seed)` with `SENSITIVITY_RANDOM_SEED = 42`.
  Regeneration reproduced the expected sensitivity files.
- Why it increases trust:
  Uncertainty is treated as a first-class output instead of a hand-wavy caveat.
- Remaining caveat, if any:
  The ranges are exploratory stress-test bands, not calibrated uncertainty distributions.

### What looks solid

- The codebase passed local tests and the full pipeline reran successfully from the repo-local `.venv`.
- Evidence:
  `./.venv/bin/python -m pytest -q` passed `12` tests.
  `./.venv/bin/python -m eu_forest_biomass_tradeoff_explorer.pipeline` completed and rewrote current outputs and figures.
- Why it increases trust:
  The project is executable end to end on the audited machine.
- Remaining caveat, if any:
  The current tests cover core mechanics, not data-download integrity, provenance checks, or end-to-end output assertions.

## Critical issues

### Finding

Zero-harvest countries still receive a “best scenario” and “robust” recommendation.

- Evidence:
  `model.py` picks winners with `groupby(...).idxmax()` in `best_scenario_by_country()` without tie handling.
  Malta’s baseline has `harvest_total_m3 = 0.0`, `industrial_roundwood_m3 = 0.0`, `wood_fuel_m3 = 0.0`, and `sawnwood_m3 = 0.0`.
  In regenerated `outputs/scenario_results_by_country.csv`, Malta has `0.0` net benefit for all non-baseline scenarios, but the sensitivity output still assigns a modal best scenario with `share_best = 1.0`.
- Why it matters:
  This creates false precision in both maps and robustness interpretation.
  A country with no active baseline harvest in the model domain should not be shown as a meaningful policy recommendation.
- Recommended fix:
  Add explicit no-op handling for countries with zero baseline harvest or ties within a tolerance.
  Return `no_material_difference` or `not_applicable` instead of forcing a winner.
  Exclude those cases from robustness shares and maps, or show them in a separate category.
- Confidence level:
  High

### Finding

The NUTS-2 workflow silently drops a large part of the EU geometry layer.

- Evidence:
  `regional.py` builds the screening dataset with `geometries.merge(landcover, on="nuts2_id", how="inner")`.
  The audited run produced `211` screening regions from `244` EU NUTS-2 geometries, leaving `33` unmatched.
  Missing regions include `SE11` and `SE23` plus multiple regions in France, Italy, Spain, Poland, Portugal, Austria, Hungary, Finland, the Netherlands, and Latvia.
- Why it matters:
  The subnational results are not full-EU NUTS-2 coverage.
  Exact-ID merging across vintages can bias counts, maps, and cross-country summaries without warning.
- Recommended fix:
  Add a coverage audit step that writes a missing-region table and fails loudly when coverage falls below a threshold.
  Introduce a NUTS crosswalk or harmonize to a single release/vintage before merging.
  Record the exact supported region set in output metadata.
- Confidence level:
  High

### Finding

Missing Eurostat land-cover detail is being collapsed into literal zeros.

- Evidence:
  `regional.py` fills all subclass area columns with `0.0` after `dropna` on only `total_area_km2` and `woodland_area_km2`.
  In the regenerated screening table, `103` regions have positive woodland area but `broadleaved + coniferous + mixed = 0`.
- Why it matters:
  Zero and unknown are not the same.
  This weakens both provenance and interpretability for woodland composition and any outputs that expose those shares, such as `top_nuts2_regions`.
- Recommended fix:
  Preserve missingness separately from zero.
  Track source availability flags per land-cover component.
  Add a plausibility check that flags regions where woodland exists but no subtype composition is available.
- Confidence level:
  High

### Finding

Narrative result claims are already out of sync with regenerated outputs.

- Evidence:
  `README.md` and `docs/short_research_report.md` state that the unconstrained integrated NUTS-2 screen selects `93` `Material Cascade`, `79` `Conservation Priority`, and `39` `Food-Land Safeguard` regions.
  The regenerated `outputs/nuts2_integrated_policy_priorities.csv` shows `92`, `79`, and `40`.
- Why it matters:
  This is a reproducibility and presentation failure.
  Readers cannot tell whether the docs, the code, or the outputs are the authoritative source.
- Recommended fix:
  Generate summary text from outputs or add a validation script that compares narrative claims against live CSV counts.
  Record output regeneration date and raw-data snapshot info in a run manifest.
- Confidence level:
  High

## Data provenance and quality audit

### What datasets are used?

- FAOSTAT land-use bulk download
  Local file: `data/raw/Inputs_LandUse_E_All_Data_(Normalized).zip`
  Used by: `data.py::load_land_use_inputs()`
- FAOSTAT forestry bulk download
  Local file: `data/raw/Forestry_E_All_Data_(Normalized).zip`
  Used by: `data.py::load_forestry_inputs()`
- Eurostat GISCO country geometry
  Local file: `data/raw/CNTR_RG_20M_2024_4326.geojson`
  Used by: `data.py::load_country_geometries()`
- Eurostat GISCO NUTS-2 geometry
  Local file: `data/raw/NUTS_RG_20M_2024_4326_LEVL_2.geojson`
  Used by: `regional.py::load_nuts2_geometries()`
- Eurostat `lan_lcv_ovw`
  Local file: `data/raw/lan_lcv_ovw.json`
  Used by: `regional.py::load_nuts2_landcover_context()`
- Eurostat `apro_cpsh1`
  Local file: `data/raw/apro_cpsh1_selected_2024.json`
  Used by: `data.py::load_crop_production_profile()`
- SLU forest area metadata and data
  Local files:
  `data/raw/sweden_slu_area_metadata.json`
  `data/raw/sweden_slu_area_2022.json`
- SLU increment metadata and data
  Local files:
  `data/raw/sweden_slu_increment_metadata.json`
  `data/raw/sweden_slu_increment_2019.json`
- SLU biomass metadata and data
  Local files:
  `data/raw/sweden_slu_biomass_metadata.json`
  `data/raw/sweden_slu_biomass_2022.json`
  Used by: `sweden.py`

### Where do they come from?

- FAOSTAT and Eurostat source URLs are declared in `config.py`.
- SLU responses are fetched through the SLU PxWeb API described in `config.py` and downloaded by `sweden.py`.
- Eurostat JSON-stat and SLU JSON files contain internal metadata such as `updated`, dataset identifiers, and labels.

### Is the source clearly documented?

- Yes, partly.
- Evidence:
  README and methods docs name the source systems and describe their role.
  `config.py` contains concrete URLs for FAOSTAT, GISCO, and Eurostat.
  Raw Eurostat and SLU JSON files embed source metadata.
- Caveat:
  There is no dedicated provenance manifest tying each derived output to exact raw files, hashes, or provider update timestamps.

### Are files raw, processed, or derived?

- Raw:
  `data/raw/*`
- Processed:
  `data/processed/*`
- Derived analysis outputs:
  `outputs/*`
- Derived presentation artifacts:
  `figures/*`
  `docs/chalmers_application_brief.pdf`

### Are there risks of undocumented manual edits?

- Yes, moderate.
- Evidence:
  Derived outputs are committed as plain CSV/GeoJSON/PNG files with fixed names and no machine-readable generation manifest.
  The working directory is not a Git repository, so file history cannot be verified.
- Why it matters:
  A reviewer cannot distinguish scripted regeneration from manual touch-up by looking only at the repository contents.

### Are units, temporal/spatial coverage, CRS, categories, and variable meanings documented?

- Mostly yes for the main methodology.
- Evidence:
  `docs/methods_note.md` and `docs/assumptions.md` explain:
  EU country scope
  NUTS-2 screening scope
  2024 country data
  2022 regional land-cover layer
  Sweden 2022 / 2019 sub-study inputs
  GeoJSON outputs carry explicit CRS metadata.
- Caveat:
  Processed CSVs themselves do not ship with sidecar metadata or dictionaries.
  Variable semantics remain embedded in code and prose rather than attached to the datasets.

### Are joins, merges, and filters traceable?

- Partly.
- Good:
  Code paths are explicit and readable.
  FAOSTAT variables and filters are defined in `config.py`.
- Weak:
  The NUTS-2 merge strategy does not emit a region-coverage report.
  NUTS vintage mismatches are not handled with a crosswalk.
  JSON-stat quality/status flags are ignored.

### Are missing values, duplicates, outliers, and invalid records handled?

- Mixed.
- Good:
  `build_baseline_inputs()` checks for missing required FAOSTAT columns before continuing.
  FAOSTAT duplicate key rows were not found in the audited raw files.
- Weak:
  Many JSON-stat missing values are turned into zeros.
  `build_baseline_metrics()` performs multiple divisions without defensive zero handling.
  Malta produces `NaN` in `wood_fuel_share` and `material_recovery_ratio`.
  No explicit outlier checks are present.
  No source-status flags are propagated.

### Are assumptions explicit or hidden in code?

- Mostly explicit, but some important ones still live only in code.
- Explicit in docs:
  scenario percentages
  carbon price
  food-land safeguard structure
  Sweden biomass carbon fraction
- Code-only or weakly surfaced:
  exact output overwrite behavior
  tie-breaking behavior in winner selection
  strict exact-ID merge behavior for NUTS-2
  implicit use of country medians in opportunity-cost scaling

### Signs that data quality checks are weak, absent, or inconsistent

- `regional.py` fills many missing subclass values with zero
- `data.py` ignores Eurostat `status` codes such as provisional and estimated
- processed and output tables do not include provenance fields
- no checksum or raw snapshot manifest exists
- NUTS-2 coverage loss is silent unless the user inspects the row counts

## Results reliability audit

### Can results be regenerated from available inputs?

- Yes, on the audited machine.
- Evidence:
  The repo-local `.venv` successfully ran:
  `python -m pytest -q`
  `python -m eu_forest_biomass_tradeoff_explorer.pipeline`
  `python -m eu_forest_biomass_tradeoff_explorer.application_brief`
- Caveat:
  This proves current executability, not historical identity of previously distributed results.

### Are there risks of silent errors?

- Yes.

### Finding

Fixed output filenames overwrite prior runs without preserving run identity.

- Evidence:
  `_write_outputs()` always writes the same filenames under `data/processed`, `outputs`, and `figures`.
- Why it matters:
  Results can drift silently when upstream raw data are revised or when parameters change.
- Recommended fix:
  Write a run manifest and optionally a timestamped run directory, or at minimum snapshot hashes and metadata alongside outputs.
- Confidence level:
  High

### Finding

Output selection logic silently resolves ties as winners.

- Evidence:
  `best_scenario_by_country()` uses `idxmax()` and never checks whether the top two scenarios are meaningfully different.
- Why it matters:
  Low-information or zero-information cases become overinterpreted as firm policy recommendations.
- Recommended fix:
  Implement tolerance-aware tie detection and a null category.
- Confidence level:
  High

### Finding

NUTS-2 results depend on an exact merge between mismatched regional data products.

- Evidence:
  `build_nuts2_screening_dataset()` performs an `inner` merge on exact `nuts2_id`.
  The audited run covered only `211/244` EU NUTS-2 geometries.
- Why it matters:
  Regional counts and maps are only valid for the surviving subset.
- Recommended fix:
  Add a region-coverage QA artifact and crosswalk handling.
- Confidence level:
  High

### Are there risks of hidden preprocessing or notebook-only logic?

- Low.
- Evidence:
  The notebook only reads outputs and does not reproduce analysis logic.
- Why it matters:
  This is a major reassurance point.

### Are there hard-coded paths?

- Code: mostly no.
- Docs: yes.
- Evidence:
  Core code uses `PROJECT_ROOT` and relative paths.
  README and several docs embed absolute `/home/zelphar/...` links.
- Why it matters:
  The computational workflow is portable, but the documentation rendering is not.

### Are there stale results that may not match current code?

- Yes, at least at the narrative layer.
- Evidence:
  README and `docs/short_research_report.md` disagree with current regenerated unconstrained NUTS-2 counts.
- Why it matters:
  Readers may quote obsolete result statements even if CSVs are current.

## Scientific and methodological concerns

### Finding

The project presents a strong screening framework, but some rankings are more structurally fragile than the prose currently suggests.

- Evidence:
  The Sweden empirical comparison materially changes regional values without changing the overall best scenario.
  Several countries have narrow robustness margins.
  Regional results inherit country-level scenario values except in Sweden.
- Why it matters:
  This is appropriate for screening, but not for strong causal or regional policy inference.
- Recommended fix:
  Make the distinction between “policy screening”, “proxy ranking”, and “empirical subnational rerun” even more explicit in top-level docs and figure captions.
- Confidence level:
  High

### Finding

`Food-Land Safeguard` is analytically useful, but its interpretation depends heavily on proxy construction choices.

- Evidence:
  The safeguard combines cropland and grassland shares, feed-land shares, permanent crops, and a country-level crop-intensity transfer.
  It is not a regional agricultural emissions inventory.
- Why it matters:
  Regions can be classified as food-land priorities because of proxy structure, not because direct regional agricultural climate evidence was observed.
- Recommended fix:
  Add sensitivity analysis for food-land proxy coefficients and report how many regional selections switch under those perturbations.
- Confidence level:
  High

### Finding

The country-specific forest opportunity-cost factor is transparent, but still empirically light.

- Evidence:
  It is scaled from EU medians of harvest intensity and carbon density rather than calibrated against direct forest carbon dynamics.
- Why it matters:
  The sign and relative magnitude of scenario rankings may be robust, but their absolute values should not be overread.
- Recommended fix:
  Add a sensitivity or validation note specifically about ranking stability under alternative opportunity-cost formulas.
- Confidence level:
  Medium

### Finding

Using total land area as the denominator for regional policy value changes the interpretation of “best” regions.

- Evidence:
  Regional policy selection uses `policy_value_eur_per_ha_land`, not per forest hectare or per target hectare.
- Why it matters:
  This favors some kinds of communication and spatial comparability, but it can also reorder regions relative to forest-area-normalized or agricultural-target-normalized metrics.
- Recommended fix:
  Publish at least one alternative normalization table or a sensitivity note explaining why total-land normalization is the headline metric.
- Confidence level:
  Medium

## Reproducibility review

### Current state

- Positive:
  the workflow is scriptable
  the main results can be regenerated from local raw files
  the sensitivity layer is seeded
  raw, processed, outputs, and figures are physically separated
- Weak:
  no run manifest
  no lock file or exported environment spec
  no Git history in the audited directory
  no data-provenance table in the repo before this audit
  no automated check that docs match outputs

### Verification performed during this audit

- `./.venv/bin/python -m pytest -q` -> `12 passed`
- `./.venv/bin/python -m eu_forest_biomass_tradeoff_explorer.pipeline` -> succeeded
- `./.venv/bin/python -m eu_forest_biomass_tradeoff_explorer.application_brief` -> succeeded

### What could not be verified

- Whether the pre-audit outputs were identical to current outputs before regeneration
- Whether any files were historically edited manually
- Any commit-based change history

## Recommended upgrades

### Critical fixes

1. Add tie and zero-baseline handling to country and regional winner selection.
2. Add explicit NUTS-2 coverage validation and region-mismatch reporting.
3. Stop flattening missing Eurostat land-cover detail into numeric zero.
4. Add a run manifest capturing parameters, raw file hashes, provider timestamps, and execution time.
5. Add a docs-to-results validation step so headline counts cannot drift silently.

### High-value upgrades

1. Move runtime parameters out of hard-coded constants into a config file or CLI arguments, while still preserving a documented default run.
2. Split runtime dependencies from dev dependencies in `pyproject.toml`; move `pytest` to an optional `dev` extra.
3. Add tests for:
   - NUTS-2 coverage expectations
   - no-op/tie handling
   - raw-data QA invariants
   - docs summary consistency
4. Record source quality/status flags from Eurostat JSON-stat instead of discarding them.
5. Separate core project docs from Chalmers application materials so the research repo reads cleanly on its own.
6. Add structured logging around data download, coverage, and output generation.

### Optional polish

1. Remove distributed build artifacts from the shared project directory.
2. Add dataset dictionaries for processed CSVs.
3. Add a compact Makefile or task runner for `test`, `run-pipeline`, and `build-brief`.
4. Add figure-to-output lineage notes or a machine-readable artifact map.

## Priority-ranked action plan

### Immediate

- Fix tie handling for no-op cases like Malta.
- Add NUTS-2 coverage and missing-region reporting.
- Preserve missing-vs-zero for Eurostat land-cover detail.
- Update narrative docs to match regenerated outputs.
- Add run metadata and provenance capture.

### Next

- Add dev extras and a lock/exported environment.
- Expand tests beyond model mechanics into data QA and result validation.
- Separate application-specific docs from core scientific documentation.
- Add parameterized execution instead of relying only on hard-coded defaults.

### Later

- Add food-land proxy sensitivity analysis.
- Add alternative regional normalization views.
- Generalize empirical subnational treatment beyond Sweden.
- Add richer agricultural and ecological validation layers.
