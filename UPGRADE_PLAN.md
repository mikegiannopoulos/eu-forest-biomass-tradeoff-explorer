# Upgrade Plan

## Roadmap

### Title

Tie-aware scenario selection and null-case handling

- Why it matters:
  Countries or regions with zero baseline harvest or numerically indistinguishable scores should not receive artificial “best scenario” labels.
- Affected files:
  `src/eu_forest_biomass_tradeoff_explorer/model.py`
  `src/eu_forest_biomass_tradeoff_explorer/sensitivity.py`
  `src/eu_forest_biomass_tradeoff_explorer/plotting.py`
  `README.md`
- Proposed change:
  Add tolerance-aware winner selection that returns `no_material_difference` or `not_applicable` for ties and no-op baselines.
  Exclude those cases from robustness shares or plot them with a distinct neutral category.
- Priority:
  Critical
- Effort level:
  Medium
- Expected benefit:
  Removes misleading policy interpretation from low-information cases such as Malta.

### Title

NUTS-2 coverage audit and crosswalk handling

- Why it matters:
  The current subnational workflow silently reduces EU NUTS-2 coverage from `244` to `211` regions.
- Affected files:
  `src/eu_forest_biomass_tradeoff_explorer/regional.py`
  `src/eu_forest_biomass_tradeoff_explorer/pipeline.py`
  `docs/methods_note.md`
- Proposed change:
  Emit a `missing_nuts2_regions.csv` artifact, fail loudly below a configured coverage threshold, and add a crosswalk or harmonized NUTS release strategy.
- Priority:
  Critical
- Effort level:
  Medium
- Expected benefit:
  Makes regional coverage explicit and prevents silent scope drift.

### Title

Preserve missing-versus-zero in Eurostat land-cover parsing

- Why it matters:
  Many regions currently appear to have zero woodland subtype composition because missing values are filled with `0.0`.
- Affected files:
  `src/eu_forest_biomass_tradeoff_explorer/regional.py`
  `data/processed/nuts2_screening_metrics.csv`
- Proposed change:
  Keep missing subclass fields as `NaN`, add availability flags, and add a QA check for impossible combinations such as positive woodland with zero subtype total.
- Priority:
  Critical
- Effort level:
  Medium
- Expected benefit:
  Improves data integrity and prevents provenance loss in regional screening outputs.

### Title

Run manifest and provenance capture

- Why it matters:
  Outputs are currently overwritten in place with no machine-readable record of data snapshot or parameter state.
- Affected files:
  `src/eu_forest_biomass_tradeoff_explorer/pipeline.py`
  `src/eu_forest_biomass_tradeoff_explorer/data.py`
  `src/eu_forest_biomass_tradeoff_explorer/sweden.py`
- Proposed change:
  Write a JSON manifest per run containing:
  raw file paths
  file hashes
  provider metadata timestamps where available
  parameter values
  execution timestamp
  Python/package versions
- Priority:
  Critical
- Effort level:
  Medium
- Expected benefit:
  Turns current “rerunnable” behavior into traceable reproducibility.

### Title

Automated narrative-to-output validation

- Why it matters:
  README and report text have already drifted from the actual regenerated counts.
- Affected files:
  `README.md`
  `docs/short_research_report.md`
  `tests/`
- Proposed change:
  Add a validation script or pytest check that reads current outputs and verifies headline counts used in docs.
  Optionally generate those lines from templates.
- Priority:
  Critical
- Effort level:
  Low
- Expected benefit:
  Prevents stale claims and keeps presentation aligned with code.

### Title

Move runtime parameters into user-facing config

- Why it matters:
  All core assumptions are hard-coded in `config.py`, which is deterministic but awkward for systematic reruns.
- Affected files:
  `src/eu_forest_biomass_tradeoff_explorer/config.py`
  `src/eu_forest_biomass_tradeoff_explorer/pipeline.py`
  `README.md`
- Proposed change:
  Introduce a YAML or TOML run config and optional CLI flags for year, carbon price, sensitivity sample size, and optimization floors.
  Keep the current defaults as the documented reference run.
- Priority:
  High
- Effort level:
  Medium
- Expected benefit:
  Improves maintainability, experiment management, and transparent comparison between runs.

### Title

Dependency and environment cleanup

- Why it matters:
  `pytest` is currently a runtime dependency, and there is no lock file or exportable environment spec.
- Affected files:
  `pyproject.toml`
  repo root
- Proposed change:
  Move testing tools to an optional `dev` extra.
  Add a lock file or documented environment export.
  Record the validated environment in reproducibility docs.
- Priority:
  High
- Effort level:
  Low
- Expected benefit:
  Cleaner installs and stronger environment reproducibility.

### Title

Expand tests to cover data QA and end-to-end scientific invariants

- Why it matters:
  Current tests are useful but concentrated in a single file and do not validate coverage, provenance, or doc consistency.
- Affected files:
  `tests/test_model.py`
  new test modules under `tests/`
- Proposed change:
  Add tests for:
  NUTS coverage expectations
  tie handling
  no missing output columns
  invariant counts for policy option sets
  narrative summary consistency
- Priority:
  High
- Effort level:
  Medium
- Expected benefit:
  Catches scientific-output regressions, not just code regressions.

### Title

Capture Eurostat status and quality flags

- Why it matters:
  Provisional, estimated, and definition-different values are currently ingested as plain floats with no trace.
- Affected files:
  `src/eu_forest_biomass_tradeoff_explorer/data.py`
  `src/eu_forest_biomass_tradeoff_explorer/regional.py`
  processed outputs
- Proposed change:
  Parse and preserve JSON-stat status codes, surface them in QA summaries, and optionally warn when high-impact outputs depend on flagged values.
- Priority:
  High
- Effort level:
  Medium
- Expected benefit:
  Stronger scientific defensibility and better data provenance.

### Title

Separate research docs from application docs

- Why it matters:
  The `docs/` folder currently mixes scientific notes with Chalmers-specific application artifacts.
- Affected files:
  `docs/`
- Proposed change:
  Move `docs/chalmers_*` into a dedicated `application/` or `portfolio/` folder, leaving `docs/` for project methods, provenance, reproducibility, and validation.
- Priority:
  High
- Effort level:
  Low
- Expected benefit:
  Cleaner project presentation for reviewers and collaborators.

### Title

Add structured logging and QA summaries

- Why it matters:
  The pipeline currently logs very little outside the optimization step.
- Affected files:
  `src/eu_forest_biomass_tradeoff_explorer/pipeline.py`
  `src/eu_forest_biomass_tradeoff_explorer/data.py`
  `src/eu_forest_biomass_tradeoff_explorer/regional.py`
- Proposed change:
  Log raw-data presence, download actions, country coverage, NUTS coverage, zero/NaN diagnostics, and output-write completion.
- Priority:
  Optional
- Effort level:
  Low
- Expected benefit:
  Faster debugging and clearer audit trails.

### Title

Repository hygiene cleanup

- Why it matters:
  The shared project directory currently contains `.venv`, `.pytest_cache`, `__pycache__`, and `.egg-info`.
- Affected files:
  repo root
  `src/`
  `tests/`
- Proposed change:
  Remove generated artifacts from the shared repository snapshot and keep only source, docs, and intentional outputs.
- Priority:
  Optional
- Effort level:
  Low
- Expected benefit:
  Better presentation and smaller, cleaner repository distribution.
