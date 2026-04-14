# Parameter Grounding Note

## Purpose

This note explains how the project's key proxy parameters relate to published literature. The goal is not to claim that the model reproduces any one paper. The goal is to show that the parameterization sits within a defensible research conversation rather than being arbitrarily chosen.

## Overall Framing

The project uses three kinds of proxy parameters:

1. `Forest carbon opportunity cost`
   Intended to represent the climate value of leaving additional biomass standing rather than harvesting it.

2. `Substitution benefits`
   Intended to represent the avoided emissions from using wood in place of more emission-intensive materials or fossil energy.

3. `Supply-chain emissions`
   Intended to represent upstream harvesting, processing, and transport emissions.

The model keeps these three terms separate because the literature shows they are conceptually different and often operate on different magnitudes.

## Project Values and Sensitivity Ranges

| Parameter | Default | Sensitivity range | Why this is defensible |
| --- | ---: | ---: | --- |
| Base forest carbon opportunity cost | 0.60 tCO2e/m3 | 0.45 to 0.75 | Intended as a middle screening value consistent with literature emphasizing large overlooked carbon costs of harvest and land-use opportunity costs. |
| Material substitution benefit | 1.10 tCO2e/m3 | 0.90 to 1.30 | Chosen to be meaningfully positive, but conservative relative to high substitution claims in the literature. |
| Bioenergy substitution benefit | 0.40 tCO2e/m3 | 0.20 to 0.60 | Lower than material substitution to reflect more contested and context-dependent mitigation outcomes for forest bioenergy. |
| Material supply-chain emissions | 0.08 tCO2e/m3 | 0.05 to 0.10 | Kept small relative to land-carbon terms, but not negligible. |
| Bioenergy supply-chain emissions | 0.10 tCO2e/m3 | 0.10 to 0.16 | Slightly higher than material supply chains because direct energy pathways often involve lower-value feedstocks and dedicated logistics. |

## Literature Grounding by Parameter Group

### 1. Forest carbon opportunity cost

The project's carbon opportunity-cost logic is grounded primarily in the idea that the climate effect of biomass harvest is not just the emissions along the product chain, but also the foregone carbon storage that would have remained or accumulated on the land if harvest were lower.

Two especially relevant sources are:

- Searchinger et al. (2018), which argues that land-use evaluation should account for the carbon-storage opportunity of land rather than only direct emissions.
- Peng et al. (2023), which shows that wood harvest can impose substantial carbon costs that are often undercounted in standard accounting approaches.

That literature does not hand us one universal `tCO2e/m3` factor. Instead, it supports the modeling choice to:

- include a separate forest-carbon term,
- allow that term to vary by context,
- keep it large enough to materially affect scenario rankings.

That is why the project makes the opportunity-cost factor country-specific and links it to observed harvest intensity and carbon density.

### 2. Material substitution benefit

The material-substitution coefficient is informed by two linked findings in the literature:

- wood-product substitution can generate meaningful avoided emissions,
- the size of that benefit varies strongly with system boundaries, product choice, and assumptions about counterfactual materials.

Sathre and O'Connor (2010) remains a landmark meta-analysis showing wide variation in displacement factors across studies. Howard et al. (2021) then shows why those substitution claims are highly assumption-sensitive and should not be treated as universal constants.

The implication for this project is straightforward:

- material substitution should usually score better than direct bioenergy,
- but the parameter should be set conservatively and tested over a range.

The project's `0.90 to 1.30 tCO2e/m3` sensitivity band is intentionally moderate rather than aggressive.

### 3. Bioenergy substitution benefit

The forest-bioenergy literature is more contested than the wood-material literature because the climate effect depends heavily on:

- baseline choice,
- feedstock type,
- counterfactual fossil fuel,
- forest regrowth timing,
- time horizon.

Buchholz et al. (2016) shows that accounting choices strongly shape apparent carbon payback outcomes in forest bioenergy studies. The IEA's recent bioenergy analysis also emphasizes that sustainable bioenergy can play a role, but land-use and biodiversity trade-offs constrain expansion and require careful feedstock choices.

That is why this project assigns bioenergy a lower avoided-emissions benefit than material use and treats the term as highly uncertain.

### 4. Supply-chain emissions

The project keeps supply-chain emissions materially smaller than the forest carbon opportunity-cost term. That choice is consistent with forest operations literature showing that harvest and transport emissions are real but often much smaller than the carbon consequences of changing biomass removal itself.

Examples include:

- Kühmaier et al. (2022) on Austrian forest supply-chain emissions,
- Kärhä et al. (2024), which reviews fuel use and direct CO2 emissions in mechanized roundwood harvesting.

That is the main reason the model treats supply-chain emissions as a lower-order term while still including them explicitly.

## Why The Project Does Not Simply Copy Literature Values

This repository is a portfolio project, not a meta-analysis or calibrated forest-sector model. The published literature uses different:

- units,
- product scopes,
- time horizons,
- baselines,
- geographic contexts,
- accounting conventions.

Using one paper's point estimate as if it were universally valid would be less defensible than using transparent middle-range values and showing sensitivity around them.

## How This Improves The Project

This note strengthens the project in three ways:

- it shows the assumptions are anchored in published debates,
- it justifies why sensitivity analysis is necessary,
- it makes clear that the project understands the distinction between proxy modeling and empirical estimation.

## References

- Eurostat. `Land cover overview by NUTS 2 region (lan_lcv_ovw)`. https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lan_lcv_ovw?lang=EN
- Searchinger, T. D., Wirsenius, S., Beringer, T., and Dumas, P. (2018). *Assessing the efficiency of changes in land use for mitigating climate change*. Nature. https://doi.org/10.1038/s41586-018-0757-z
- Peng, L., Searchinger, T. D., Zionts, J., et al. (2023). *The carbon costs of global wood harvests*. Nature. https://doi.org/10.1038/s41586-023-06187-1
- Sathre, R., and O'Connor, J. (2010). *Meta-analysis of greenhouse gas displacement factors of wood product substitution*. Environmental Science & Policy. https://doi.org/10.1016/j.envsci.2009.12.005
- Howard, C., Dymond, C. C., Griess, V., et al. (2021). *Wood product carbon substitution benefits: a critical review of assumptions*. Carbon Balance and Management. https://doi.org/10.1186/s13021-021-00171-w
- Buchholz, T., Hurteau, M. D., Gunn, J., and Saah, D. (2016). *A global meta-analysis of forest bioenergy greenhouse gas emission accounting studies*. GCB Bioenergy. https://doi.org/10.1111/gcbb.12245
- Kühmaier, M., Kral, I., and Kanzian, C. (2022). *Greenhouse Gas Emissions of the Forest Supply Chain in Austria in the Year 2018*. Sustainability. https://doi.org/10.3390/su14020792
- Kärhä, K., Eliasson, L., Kühmaier, M., and Spinelli, R. (2024). *Fuel Consumption and CO2 Emissions in Fully Mechanized Cut-to-Length Harvesting Operations of Industrial Roundwood: A Review*. Current Forestry Reports. https://doi.org/10.1007/s40725-024-00219-3

