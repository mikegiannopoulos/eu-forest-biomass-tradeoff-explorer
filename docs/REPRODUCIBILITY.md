# Reproducibility

## Verified workflow on the audited machine

The following commands were run successfully from the repo-local `.venv` during the audit on `2026-04-14`:

```bash
./.venv/bin/python -m pytest -q
./.venv/bin/python -m eu_forest_biomass_tradeoff_explorer.pipeline
./.venv/bin/python -m eu_forest_biomass_tradeoff_explorer.application_brief
```

Observed outcomes:

- tests passed: `12`
- the pipeline regenerated current `data/processed/`, `outputs/`, and `figures/` artifacts
- the application PDF was rebuilt at `docs/chalmers_application_brief.pdf`

## Current reproducibility strengths

- Source code is organized as a Python package instead of notebook-only logic.
- The main workflow is deterministic under the default configuration.
- Sensitivity analysis uses a fixed seed.
- Raw data are stored locally once downloaded.
- The notebook is presentation-only and does not hold hidden analysis logic.

## Current reproducibility weaknesses

- The working directory is not inside a Git repository, so commit-based provenance could not be verified.
- Outputs are overwritten in place under fixed filenames.
- There is no machine-readable run manifest.
- There is no lock file or exported environment spec beyond `pyproject.toml`.
- Narrative docs can drift from actual outputs unless checked manually.

## Recommended standard run procedure

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m pytest -q
python -m eu_forest_biomass_tradeoff_explorer.pipeline
python -m eu_forest_biomass_tradeoff_explorer.application_brief
```

## What reproducibility currently means in this repo

At present, “reproducible” means:

- the current code can regenerate the current outputs from the locally available raw inputs on the audited machine

It does **not yet** mean:

- every output can be tied to a specific code commit
- every output carries a run ID or raw-file hash
- every narrative statement in docs is guaranteed to match the current outputs

## Recommended next step

Implement a run manifest and output validation layer so each regeneration records:

- raw file hashes
- source update timestamps
- model parameters
- software environment
- output hashes
- any coverage or missing-data warnings
