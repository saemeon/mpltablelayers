"""# Shading, censoring, header spans, and annotations on a plottable table

Four overlay layers using ``add_plottable_multispan_cell`` and
``add_plottable_cell_annotation``:

- light blue **background shading** over a group of rows
- black **censored region** with diagonal text
- **two-level spanning header**: full-width title (y=-2) + Scores sub-header (y=-1)
- **ellipse annotation** calling out a single outstanding cell
"""

# %%
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle
from plottable import Table

from mpltablelayers import add_plottable_cell_annotation, add_plottable_multispan_cell

df = pd.DataFrame(
    {
        "Math": [85, 92, 78, 95, 88, 73, 91, 67],
        "Science": [90, 85, 82, 88, 79, 95, 84, 76],
        "English": [78, 88, 91, 72, 94, 81, 86, 90],
        "Grade": ["B", "A", "B", "A", "B", "B", "A", "C"],
    },
    index=pd.Index(
        ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank", "Grace", "Henry"],
        name="Name",
    ),
)

fig, ax = plt.subplots(figsize=(7, 5))

# Col layout: 0=Name(index) 1=Math 2=Science 3=English 4=Grade
tab = Table(df, ax=ax)

# ── Layer 1: background shading ──────────────────────────────────────────────
# light blue over Group A (data rows 0–3, all 5 cols)
add_plottable_multispan_cell(tab, row=0, col=0, width=5, height=4, facecolor="#d4e6f1")

# ── Layer 2: censored region ─────────────────────────────────────────────────
# black out data rows 4–5, score cols 1–3
add_plottable_multispan_cell(tab, row=4, col=1, width=3, height=2, facecolor="black")
c_tl, c_br = tab.cells[(4, 1)], tab.cells[(5, 3)]
ax.text(
    (c_tl.x + c_br.x + c_br.width) / 2,
    (c_tl.y + c_br.y + c_br.height) / 2,
    "REDACTED",
    color="white",
    rotation=30,
    ha="center",
    va="center",
    fontsize=8,
    weight="bold",
    zorder=4,
)

# ── Layer 3a: full-width title header (one row above col_label_row) ──────────
# The col_label_row sits at y=-1; extend ylim to reveal y=-2 for the title.
b, t = ax.get_ylim()  # inverted axis: b > t
ax.set_ylim(b, t - 1)  # shift top to t-1, making y=-2 visible

ax.add_patch(Rectangle((0, -2), 5, 1, facecolor="#1a5276", zorder=3, linewidth=0))
ax.text(
    2.5,
    -1.5,
    "Student Performance",
    color="white",
    ha="center",
    va="center",
    fontsize=11,
    weight="bold",
    zorder=4,
)

# ── Layer 3b: "Scores" sub-header (col_label_row, cols 1–3) ─────────────────
add_plottable_multispan_cell(tab, row=-1, col=1, width=3, height=1, facecolor="#2980b9")
h1, h3 = tab.col_label_row.cells[1], tab.col_label_row.cells[3]
ax.text(
    (h1.x + h3.x + h3.width) / 2,
    (h1.y + h3.y + h3.height) / 2,
    "Scores",
    color="white",
    ha="center",
    va="center",
    fontsize=9,
    weight="bold",
    zorder=4,
)

# ── Layer 4: ellipse annotation calling out Dave's Math score (95) ───────────
# Data rows 0-indexed: Dave = row 3, Math = col 1
ann = add_plottable_cell_annotation(
    tab, row=3, col=1, edgecolor="#c0392b", linewidth=2.5, padding=0
)
ax.annotate(
    "Top score!",
    xy=(1, 0.5),
    xycoords=ann,
    xytext=(1.05, 0.45),
    textcoords="axes fraction",
    color="#c0392b",
    fontsize=8,
    weight="bold",
    annotation_clip=False,
    arrowprops=dict(
        arrowstyle="->", color="#c0392b", lw=1.5, connectionstyle="arc3,rad=0.3"
    ),
)

_ = plt.tight_layout()
