# Results Validation

## Scope

This note records what was validated directly during the audit, what was confirmed, and what remains uncertain.

## Validation performed

### Code execution

- `./.venv/bin/python -m pytest -q`
  Result: `12 passed`
- `./.venv/bin/python -m eu_forest_biomass_tradeoff_explorer.pipeline`
  Result: completed successfully
- `./.venv/bin/python -m eu_forest_biomass_tradeoff_explorer.application_brief`
  Result: completed successfully

### Output regeneration

The pipeline regenerated current CSV and PNG artifacts on `2026-04-14` in a consistent time window.

### Structural checks

- baseline countries: `27`
- scenario result rows: `108` = `27 countries x 4 scenarios`
- screening regions: `211`
- unconstrained policy rows: `211`
- optimized portfolio rows: `211`
- Swedish empirical comparison rows: `6`
- duplicate `nuts2_id` rows in screening, policy, and optimized outputs: `0`

### Headline counts confirmed from current outputs

- best scenario by country:
  `15` `Material Cascade`
  `12` `Conservation Priority`
- EU-wide sensitivity best frequency:
  `56%` `Material Cascade`
  `44%` `Conservation Priority`
- Sweden empirical best scenarios:
  `8` `Material Cascade`
- unconstrained integrated NUTS-2 priorities:
  `92` `Material Cascade`
  `79` `Conservation Priority`
  `40` `Food-Land Safeguard`
- optimized portfolio:
  `123` `Material Cascade`
  `34` `Conservation Priority`
  `54` `Food-Land Safeguard`

## Confirmed reliability issues

### Malta null-case artifact

- Baseline harvest, industrial roundwood, wood fuel, and sawnwood are all `0.0`.
- All three non-baseline scenarios therefore evaluate to `0.0`.
- The current winner-selection logic still assigns Malta a best forest scenario.

Interpretation:
This is a ranking artifact, not meaningful evidence.

### NUTS-2 coverage loss

- GISCO 2024 NUTS-2 geometry contains `244` EU rows in the audited scope.
- The screening dataset contains `211` rows.
- Missing regions include `SE11` and `SE23` plus multiple regions in France, Italy, Spain, Poland, Portugal, Austria, Hungary, Finland, the Netherlands, and Latvia.

Interpretation:
Subnational results currently apply only to the matched subset.

### Land-cover missingness flattened to zero

- `103` screening rows have positive woodland area but zero broadleaved + coniferous + mixed woodland detail.

Interpretation:
At least some subclass context is being treated as zero when it is more plausibly missing or incompatible.

### Narrative drift

- Current outputs show unconstrained counts of `92 / 79 / 40`.
- README and report prose still state `93 / 79 / 39`.

Interpretation:
Text claims are not automatically synchronized with current outputs.

## What looks validated

- The package runs end to end on the audited machine.
- Country-level summary outputs are internally consistent with baseline country count and scenario count.
- The optimization constraint summary is internally consistent and reports successful solver termination.
- The notebook is not a hidden source of alternative logic.

## What remains unverified

- Historical identity of outputs prior to regeneration
- Commit-level provenance
- Whether any files were manually edited before the audit
