# Consistency Audit

## SE22 trace

The SE22 discrepancy is valid model behavior, not a hidden numerical inconsistency.

- Sweden empirical forest-only result: `Material Cascade` at `5.333430 EUR/forest ha`.
- Integrated NUTS-2 result: `Food-Land Safeguard` at `1.666945 EUR/land ha`.
- Best forest option inside the integrated screen: `Material Cascade` at `1.627670 EUR/land ha`.
- Food-land safeguard value in SE22: `1.666945 EUR/land ha`.
- Integrated food-versus-forest margin in SE22: `0.039275 EUR/land ha`.
- Optimized portfolio result: `Food-Land Safeguard` with `switch_from_unconstrained = False`.

Interpretation:
The Sweden empirical map compares only forest scenarios and reports value per forest hectare. The integrated and optimized maps compare a larger policy space that includes Food-Land Safeguard and rank options by value per hectare of total land. SE22 keeps Material Cascade as its best forest option, but Food-Land Safeguard is slightly better once agricultural land competition is included.

## Before vs after

- Before this audit, the outputs mixed `carbon_value_eur_per_ha` and `policy_value_eur_per_ha_land` without common aliases or policy-space flags, so SE22 looked inconsistent unless traced manually.
- After this audit, the outputs expose both `value_eur_per_forest_ha` and `value_eur_per_land_ha`, and every regional policy output carries `is_forest_only` plus `includes_food_policy`.
- The SE22 selections did not change after the audit. The correction is interpretive and traceability-focused, not a numerical reversal.

## Structural checks

- NUTS-2 regions present in geometry layer but absent from the selected land-cover join: `33`.
- Regions with woodland area but missing woodland subclass detail before zero-filling: `113`.
- Country-level forest scenario rows excluded from best-scenario selection because baseline forest activity is zero: `Malta`.

## Current portfolio counts

- Integrated priorities: 92 Material Cascade, 79 Conservation Priority, 40 Food-Land Safeguard.
- Optimized portfolio: 123 Material Cascade, 54 Food-Land Safeguard, 34 Conservation Priority.

## Conclusion

SE22 is not evidence of a silent coding error. It is evidence that the project contains two different decision frames: a forest-only empirical Sweden rerun and a broader integrated land-use comparison. The audit found real structural issues elsewhere, especially silent NUTS-2 join loss and missing-detail zero filling, but the SE22 switch itself is mathematically expected under the current model definition.
