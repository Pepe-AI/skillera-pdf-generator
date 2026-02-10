"""
Chart generation service module.
Generates horizontal bar charts for leadership dimension scores.
"""

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server use

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO

from config import Config


class ChartGenerator:
    """Service class for generating charts and visualizations."""

    def __init__(self):
        """Initialize the chart generator with brand colors."""
        self.colors_map = {
            "Avanzado": Config.CHART_COLORS["avanzado"],         # #9F7AEA
            "Intermedio": Config.CHART_COLORS["intermedio"],      # #667EEA
            "Principiante": Config.CHART_COLORS["principiante"],  # #A0AEC0
        }
        self.bg_color = Config.COLOR_BACKGROUND  # #1A1A2E

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
        # Extract data
        names = [d["name"] for d in dimensions]
        scores = [d["score"] for d in dimensions]
        levels = [dl["level"] for dl in dimension_levels]
        bar_colors = [self.colors_map.get(level, "#A0AEC0") for level in levels]

        # Create figure with dark background
        fig, ax = plt.subplots(figsize=Config.CHART_FIGSIZE, facecolor=self.bg_color)
        ax.set_facecolor(self.bg_color)

        # Horizontal bars
        y_positions = range(len(names))
        bars = ax.barh(y_positions, scores, color=bar_colors, height=0.6, edgecolor="none")

        # Score labels at end of each bar
        for bar, score in zip(bars, scores):
            ax.text(
                bar.get_width() + 1.5,
                bar.get_y() + bar.get_height() / 2,
                f"{score:.0f}%",
                va="center",
                ha="left",
                color="#FFFFFF",
                fontsize=11,
                fontweight="bold",
            )

        # Y-axis: dimension names
        ax.set_yticks(list(y_positions))
        ax.set_yticklabels(names, color="#FFFFFF", fontsize=11)
        ax.invert_yaxis()  # First dimension at top

        # X-axis: 0 to 100 with extra space for labels
        ax.set_xlim(0, 110)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.tick_params(axis="x", colors="#FFFFFF", labelsize=9)

        # Subtle grid
        ax.xaxis.grid(True, linestyle="--", alpha=0.2, color="#FFFFFF")
        ax.yaxis.grid(False)

        # Remove spines
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Legend
        legend_patches = [
            mpatches.Patch(color=self.colors_map["Avanzado"], label="Avanzado"),
            mpatches.Patch(color=self.colors_map["Intermedio"], label="Intermedio"),
            mpatches.Patch(color=self.colors_map["Principiante"], label="Principiante"),
        ]
        ax.legend(
            handles=legend_patches,
            loc="lower right",
            fontsize=9,
            facecolor=self.bg_color,
            edgecolor="#FFFFFF",
            labelcolor="#FFFFFF",
            framealpha=0.8,
        )

        plt.tight_layout(pad=1.0)

        # Render to BytesIO
        buffer = BytesIO()
        fig.savefig(
            buffer,
            format="png",
            dpi=Config.CHART_DPI,
            facecolor=fig.get_facecolor(),
            bbox_inches="tight",
        )
        plt.close(fig)  # Free memory
        buffer.seek(0)
        return buffer
