"""
Chart generation service module.
Generates horizontal bar charts for leadership dimension scores.
Matches the reference PDF design: legend on top, roman numeral labels,
transparent background for PDF integration.
"""

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server use

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO

from config import Config

# Roman numeral prefixes for dimension names
ROMAN_NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]


class ChartGenerator:
    """Service class for generating charts and visualizations."""

    def __init__(self):
        """Initialize the chart generator with brand colors."""
        self.colors_map = {
            "Avanzado": Config.CHART_COLORS["avanzado"],         # #9F7AEA
            "Intermedio": Config.CHART_COLORS["intermedio"],      # #667EEA
            "Principiante": Config.CHART_COLORS["principiante"],  # #A0AEC0
        }

    def generate_chart(
        self,
        dimensions: list[dict],
        dimension_levels: list[dict],
    ) -> BytesIO:
        """
        Generate a horizontal bar chart for leadership dimensions.

        Args:
            dimensions: List of dicts with 'name' and 'score' keys.
            dimension_levels: List of dicts with 'name' and 'level' keys.

        Returns:
            BytesIO containing a PNG image of the chart.
        """
        # Extract data and add roman numeral prefixes
        names = []
        for i, d in enumerate(dimensions):
            prefix = ROMAN_NUMERALS[i] if i < len(ROMAN_NUMERALS) else str(i + 1)
            names.append(f"{prefix}. {d['name']}")
        scores = [d["score"] for d in dimensions]
        levels = [dl["level"] for dl in dimension_levels]
        bar_colors = [self.colors_map.get(level, "#A0AEC0") for level in levels]

        # Determine x-axis max based on scores
        max_score = max(scores) if scores else 100
        if max_score <= 35:
            x_max = 35
            x_ticks = list(range(0, 40, 5))
        elif max_score <= 100:
            x_max = 100
            x_ticks = [0, 25, 50, 75, 100]
        else:
            x_max = int(max_score * 1.1)
            x_ticks = None  # Auto

        # Create figure with transparent background
        fig, ax = plt.subplots(figsize=Config.CHART_FIGSIZE)
        fig.patch.set_alpha(0.0)
        ax.set_facecolor("none")

        # ── Legend on TOP (horizontal, centered) ──────────────────────
        legend_patches = [
            mpatches.Patch(color=self.colors_map["Avanzado"], label="AVANZADO"),
            mpatches.Patch(color=self.colors_map["Intermedio"], label="INTERMEDIO"),
            mpatches.Patch(color=self.colors_map["Principiante"], label="PRINCIPIANTE"),
        ]
        legend = ax.legend(
            handles=legend_patches,
            loc="upper center",
            bbox_to_anchor=(0.5, 1.15),
            ncol=3,
            fontsize=9,
            frameon=False,
            labelcolor="#FFFFFF",
            handlelength=1.5,
            columnspacing=2.0,
        )

        # ── Horizontal bars ───────────────────────────────────────────
        y_positions = range(len(names))
        bars = ax.barh(
            y_positions, scores,
            color=bar_colors, height=0.6, edgecolor="none",
        )

        # Y-axis: dimension names with roman numerals
        ax.set_yticks(list(y_positions))
        ax.set_yticklabels(names, color="#FFFFFF", fontsize=10)
        ax.invert_yaxis()  # First dimension at top

        # X-axis
        ax.set_xlim(0, x_max)
        if x_ticks:
            ax.set_xticks(x_ticks)
        ax.tick_params(axis="x", colors="#FFFFFF", labelsize=9)

        # Subtle vertical grid lines
        ax.xaxis.grid(True, linestyle="-", alpha=0.15, color="#FFFFFF")
        ax.yaxis.grid(False)

        # Remove spines
        for spine in ax.spines.values():
            spine.set_visible(False)

        plt.tight_layout(pad=1.5)

        # Render to BytesIO with transparent background
        buffer = BytesIO()
        fig.savefig(
            buffer,
            format="png",
            dpi=Config.CHART_DPI,
            transparent=True,
            bbox_inches="tight",
        )
        plt.close(fig)  # Free memory
        buffer.seek(0)
        return buffer
