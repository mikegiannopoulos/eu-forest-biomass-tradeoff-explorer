from __future__ import annotations

import os
import textwrap
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from .config import FIGURES_DIR, OUTPUTS_DIR, PROJECT_ROOT


PAGE_WIDTH = 8.27
PAGE_HEIGHT = 11.69
MARGIN_X = 0.08
TOP_Y = 0.94


def _add_wrapped_text(fig, text: str, *, x: float, y: float, width: int, size: float, weight: str = "normal", color: str = "#1d2430") -> float:
    wrapped = "\n".join(textwrap.wrap(text, width=width))
    fig.text(x, y, wrapped, ha="left", va="top", fontsize=size, fontweight=weight, color=color, family="DejaVu Serif")
    line_count = max(1, wrapped.count("\n") + 1)
    return y - line_count * (size / 72.0) / PAGE_HEIGHT * 1.55


def _new_page():
    fig = plt.figure(figsize=(PAGE_WIDTH, PAGE_HEIGHT))
    fig.patch.set_facecolor("white")
    return fig


def _page_title(fig, title: str, subtitle: str | None = None) -> float:
    y = TOP_Y
    fig.text(MARGIN_X, y, title, ha="left", va="top", fontsize=20, fontweight="bold", color="#214f7a", family="DejaVu Serif")
    y -= 0.045
    if subtitle:
        fig.text(MARGIN_X, y, subtitle, ha="left", va="top", fontsize=10.5, color="#5c6675", family="DejaVu Serif")
        y -= 0.04
    return y


def _add_section_heading(fig, heading: str, y: float) -> float:
    fig.text(MARGIN_X, y, heading.upper(), ha="left", va="top", fontsize=10.5, fontweight="bold", color="#214f7a", family="DejaVu Sans")
    return y - 0.03


def _add_bullets(fig, bullets: list[str], y: float, *, width: int = 85, size: float = 10.3) -> float:
    for bullet in bullets:
        wrapped_lines = textwrap.wrap(bullet, width=width)
        if not wrapped_lines:
            continue
        fig.text(MARGIN_X + 0.012, y, u"\u2022", ha="left", va="top", fontsize=size + 2, color="#1d2430", family="DejaVu Serif")
        first = True
        for line in wrapped_lines:
            x = MARGIN_X + 0.032
            fig.text(x, y, line, ha="left", va="top", fontsize=size, color="#1d2430", family="DejaVu Serif")
            y -= 0.022
            if first:
                first = False
        y -= 0.005
    return y


def _add_figure_page(pdf: PdfPages, *, title: str, image_path: Path, caption: str, note: str | None = None) -> None:
    fig = _new_page()
    y = _page_title(fig, title)

    ax = fig.add_axes([0.08, 0.17, 0.84, 0.63])
    image = mpimg.imread(image_path)
    ax.imshow(image)
    ax.axis("off")

    y = 0.13
    y = _add_wrapped_text(fig, caption, x=MARGIN_X, y=y, width=112, size=10.0, weight="bold", color="#214f7a")
    if note:
        _add_wrapped_text(fig, note, x=MARGIN_X, y=y - 0.01, width=114, size=9.5, color="#5c6675")

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def build_chalmers_application_pdf(output_path: Path | None = None) -> Path:
    output = output_path or PROJECT_ROOT / "docs" / "chalmers_application_brief.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)

    with PdfPages(output) as pdf:
        fig = _new_page()
        y = _page_title(
            fig,
            "European Forest Carbon, Wood-Use, and Food-Land Trade-offs Under Constrained Regional Policy Design",
            "Application brief for the Chalmers doctoral position “Land Use and Climate Impacts”",
        )
        y = _add_wrapped_text(
            fig,
            "This brief summarizes a portfolio-scale research project built to demonstrate direct fit for the Chalmers "
            "doctoral position. The repository combines official European and FAO data, transparent carbon-accounting "
            "logic, subnational spatial analysis, and a small constrained allocation model to study trade-offs between "
            "forest carbon, wood use, food-related land capacity, and policy design.",
            x=MARGIN_X,
            y=y - 0.02,
            width=108,
            size=11.2,
        )

        y = _add_section_heading(fig, "Research Question", y - 0.03)
        y = _add_wrapped_text(
            fig,
            "How do alternative forest-biomass strategies across Europe compare when climate performance is evaluated "
            "through forest carbon retention, substitution effects, and biomass use, and how do those forestry choices "
            "interact with agricultural land that may be important for food-related production capacity?",
            x=MARGIN_X,
            y=y,
            width=110,
            size=10.6,
        )

        y = _add_section_heading(fig, "Scenario Design", y - 0.03)
        y = _add_bullets(
            fig,
            [
                "Conservation Priority: reduce total harvest by 15%, taking the cut from wood fuel first.",
                "Material Cascade: keep harvest constant but shift 20% of wood fuel volume into industrial roundwood uses.",
                "Bioenergy Push: increase total harvest by 15% and allocate the additional harvest to direct energy use.",
                "Food-Land Safeguard: assign climate value to retaining a marginal share of agricultural land against further biomass diversion.",
            ],
            y,
        )

        y = _add_section_heading(fig, "Data and Scope", y - 0.01)
        y = _add_bullets(
            fig,
            [
                "FAOSTAT land-use statistics for forest area and living biomass carbon stock.",
                "FAOSTAT forestry statistics for roundwood, industrial roundwood, wood fuel, and sawnwood production.",
                "Eurostat GISCO country and NUTS-2 geometry.",
                "Eurostat regional land-cover data for woodland, cropland, grassland, fodder, and permanent crops.",
                "Eurostat crop-production data for selected food crop area, production, and yield.",
                "Spatial domain: EU-27 countries and NUTS-2 regions. Analysis year: 2024 for country data and 2022 for the selected regional land-cover layer.",
            ],
            y,
        )

        y = _add_section_heading(fig, "Why This Matters For The Position", y - 0.01)
        _add_bullets(
            fig,
            [
                "Shows land-use and biomass systems thinking rather than generic climate visualization.",
                "Demonstrates carbon-accounting logic and scientific computing in Python.",
                "Uses European and subnational spatial data directly relevant to the advertised research scope.",
                "Adds a simple biophysical-economic allocation step instead of stopping at descriptive scenario comparison.",
            ],
            y,
        )
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        fig = _new_page()
        y = _page_title(fig, "Methods and Main Findings")
        y = _add_section_heading(fig, "Methods", y - 0.01)
        y = _add_wrapped_text(
            fig,
            "The country-level model estimates scenario performance through forest carbon retention, substitution gain, "
            "and supply-chain savings. The forest carbon opportunity-cost term is country-specific and increases where "
            "observed harvest intensity and carbon density are relatively high. A 400-draw sensitivity analysis is used "
            "to distinguish robust from assumption-sensitive results. At NUTS-2 level, country scenario values are "
            "downscaled by regional woodland share, and the agricultural side is strengthened with an official "
            "crop-production-intensity index derived from Eurostat data on cereals, pulses, potatoes, and vegetables.",
            x=MARGIN_X,
            y=y,
            width=108,
            size=10.4,
        )
        y = _add_wrapped_text(
            fig,
            "The metric basis also differs across regional layers. The Sweden empirical rerun is a forest-only "
            "comparison reported in EUR per forest hectare, while the integrated and optimized NUTS-2 policy layers "
            "compare forest and food-land options together in EUR per hectare of total land. That distinction explains "
            "why SE22 can keep Material Cascade as its best forest option while still selecting Food-Land Safeguard in "
            "the integrated screen.",
            x=MARGIN_X,
            y=y - 0.02,
            width=108,
            size=10.4,
        )
        y = _add_wrapped_text(
            fig,
            "The final extension adds a small mixed-integer allocation model that chooses exactly one option per NUTS-2 "
            "region while preserving at least 97% of baseline regionalized biomass supply and safeguarding at least 22% "
            "of available crop-capacity proxy. This is still a screening model rather than a sector-equilibrium model, "
            "but it moves the project closer to the style of biophysical-economic land-use analysis described in the "
            "Chalmers call.",
            x=MARGIN_X,
            y=y - 0.02,
            width=108,
            size=10.4,
        )

        y = _add_section_heading(fig, "Main Findings", y - 0.04)
        y = _add_bullets(
            fig,
            [
                "Material Cascade: about 18.4 MtCO2e net climate benefit relative to baseline.",
                "Conservation Priority: about 17.1 MtCO2e.",
                "Bioenergy Push: about -21.8 MtCO2e.",
                "Across 400 sensitivity runs, Bioenergy Push never becomes the best EU-wide option.",
                "Unconstrained integrated NUTS-2 screen: 92 Material Cascade, 79 Conservation Priority, 40 Food-Land Safeguard, 0 Bioenergy Push.",
                "Constrained regional portfolio: 123 Material Cascade, 34 Conservation Priority, 54 Food-Land Safeguard, 0 Bioenergy Push.",
                "45 regions switch away from their unconstrained locally best option once the Europe-wide safeguards are enforced.",
                "The optimized portfolio retains about 97.0% of baseline regionalized biomass supply and safeguards about 45.6% of available crop-capacity proxy.",
                "Total optimized portfolio value at EUR 100/tCO2: about EUR 2.15 billion.",
            ],
            y,
        )

        y = _add_section_heading(fig, "Interpretation", y - 0.01)
        _add_wrapped_text(
            fig,
            "The project’s value lies in combining forest carbon, material substitution, biomass extraction, food-land "
            "competition, subnational spatial analysis, and constrained policy selection in one transparent workflow. "
            "It shows the ability to formulate the right kind of research question and to be explicit about what the "
            "model does and does not capture.",
            x=MARGIN_X,
            y=y,
            width=108,
            size=10.4,
        )
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        _add_figure_page(
            pdf,
            title="Figure 1. EU Scenario Decomposition",
            image_path=FIGURES_DIR / "eu_scenario_decomposition.png",
            caption=(
                "The EU-level decomposition figure is the clearest entry point for a committee reader. It shows that "
                "both material cascade and conservation outperform bioenergy expansion, but for different reasons: "
                "material use gains more through substitution, while conservation gains more through avoided forest carbon loss."
            ),
            note="This figure is the best single summary of the project’s carbon-accounting logic.",
        )

        _add_figure_page(
            pdf,
            title="Figure 2. Constrained NUTS-2 Policy Map",
            image_path=FIGURES_DIR / "nuts2_optimized_policy_map.png",
            caption=(
                "The constrained NUTS-2 map demonstrates subnational spatial analysis and policy trade-off reasoning. "
                "It shows that once biomass supply and food-capacity safeguards are imposed at EU scale, the spatial "
                "portfolio shifts away from a purely local winner-takes-all ranking."
            ),
            note="This figure most directly reflects the European and sub-national trade-off language in the Chalmers advertisement.",
        )

        _add_figure_page(
            pdf,
            title="Figure 3. Constrained Portfolio Summary and PhD Extension Path",
            image_path=FIGURES_DIR / "nuts2_optimized_portfolio_summary.png",
            caption=(
                "The constrained portfolio summary shows that the project is not purely descriptive. It selects a "
                "regional policy mix under explicit biomass-supply and crop-capacity safeguards, which is much closer "
                "to the advertised need for biophysical and economic modeling."
            ),
            note=(
                "Most credible PhD extensions from this base: better subnational forestry data, direct regional "
                "agricultural production or GHG indicators, biodiversity constraints, tighter literature calibration, "
                "and a richer biophysical-economic allocation model."
            ),
        )

    return output


def main() -> None:
    output = build_chalmers_application_pdf()
    print(output)


if __name__ == "__main__":
    main()
