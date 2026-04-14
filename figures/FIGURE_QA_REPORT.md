# Figure QA Report

Scope reviewed on 2026-03-25:
- Generated figures in [`figures/`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/figures)
- Plot-generating code in [`plotting.py`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py) and [`pipeline.py`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/pipeline.py)
- Notebook [`01_country_tradeoffs.ipynb`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/notebooks/01_country_tradeoffs.ipynb), which currently contains no direct plot-generation cells

Validation performed:
- Regenerated the full figure set from the project-local `.venv`
- Ran a structural Matplotlib QA pass for tick-label overlap, annotation overlap, and legends covering plotted content
- Confirmed the final regeneration completed without errors

## Figure-by-figure audit

### `best_scenario_map.png`
- Source: [`plot_best_scenario_map()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: Legend sat on top of mapped countries, and map axes could still emit stray coordinate ticks.
- Fix applied: Moved the legend outside the plotting area and explicitly suppressed map ticks/spines with a shared map-axis helper.

### `country_tradeoff_scatter.png`
- Source: [`plot_tradeoff_scatter()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: Legend occupied the data area and the country callouts were too tightly packed.
- Fix applied: Moved the legend outside the axes, added small plot margins, and switched to staggered annotation offsets to prevent label stacking.

### `eu_scenario_decomposition.png`
- Source: [`plot_scenario_decomposition()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: Long scenario labels were crowding the x-axis in the two-panel layout.
- Fix applied: Enabled constrained layout, replaced the long scenario labels with wrapped two-line labels, and moved the component legend fully outside the title band.

### `eu_uncertainty_ranges.png`
- Source: [`plot_eu_uncertainty_ranges()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: None.
- Fix applied: No change.

### `country_robustness_heatmap.png`
- Source: [`plot_country_robustness_heatmap()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: None.
- Fix applied: No change.

### `robust_best_scenario_map.png`
- Source: [`plot_robust_best_scenario_map()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: Legend covered part of the map area.
- Fix applied: Moved the legend outside the axes and explicitly suppressed map ticks/spines.

### `nuts2_priority_map.png`
- Source: [`plot_nuts2_priority_map()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: Map-axis ticks could still appear around the choropleth.
- Fix applied: Explicitly suppressed map ticks/spines after plotting.

### `nuts2_context_scatter.png`
- Source: [`plot_nuts2_context_scatter()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: Legend sat on top of plotted points, and region annotations overlapped in the dense upper range.
- Fix applied: Moved the legend outside the axes, added plot margins, and reduced/staggered the callouts to the top two regions.

### `nuts2_integrated_policy_map.png`
- Source: [`plot_integrated_policy_priority_map()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: Legend and explanatory note were sitting on top of the map, and map ticks could still leak through.
- Fix applied: Moved the legend outside the axes, moved the note to figure-level footer text, and explicitly suppressed map ticks/spines.

### `nuts2_forest_food_tradeoff.png`
- Source: [`plot_forest_food_tradeoff()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: Legend occupied the data area and the annotated region labels overlapped.
- Fix applied: Moved the legend outside the axes, added plot margins, and reduced/staggered the callouts to the top three switching regions.

### `nuts2_integrated_policy_summary.png`
- Source: [`plot_integrated_policy_summary()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: None.
- Fix applied: No change.

### `nuts2_optimized_policy_map.png`
- Source: [`plot_optimized_policy_map()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: Legend and explanatory note were sitting on top of the map, and map ticks could still leak through.
- Fix applied: Moved the legend outside the axes, moved the note to figure-level footer text, and explicitly suppressed map ticks/spines.

### `nuts2_optimized_portfolio_summary.png`
- Source: [`plot_optimized_portfolio_summary()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: The left-panel policy labels were still too long for a compact two-panel figure, especially with value annotations above the bars.
- Fix applied: Enabled constrained layout, switched the left-panel policy labels to wrapped two-line labels, and pulled the panel-B legend down below the title with extra y-axis headroom.

### `sweden_nuts2_empirical_best_scenario_map.png`
- Source: [`plot_sweden_empirical_best_scenario_map()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: No current clipping/overlap issue in the generated gradient version.
- Fix applied: Shared map-axis suppression was applied here as well so the map stays tick-free in both gradient and categorical renders.

### `sweden_nuts2_empirical_comparison.png`
- Source: [`plot_sweden_empirical_comparison()`](/home/zelphar/projects/eu-forest-biomass-tradeoff-explorer/src/eu_forest_biomass_tradeoff_explorer/plotting.py)
- Issue detected: The panel legend covered part of the horizontal bars.
- Fix applied: Moved the legend fully outside the title band at figure level, kept constrained layout, and retained the small x-margin on the difference panel.
