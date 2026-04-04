"""# Background shading

Color a rectangular region *behind* table cells using ``add_table_multispan_cell``
with a low ``zorder`` so the cell text and borders remain visible.

The key parameter is ``zorder=-1``: values below zero place the span behind the
default table grid (zorder 0).
"""

# %%
import matplotlib.pyplot as plt
import pandas as pd

import mpltablelayers

df = pd.DataFrame(
    {
        "Product": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
        "Q1": [120, 95, 140, 88, 110],
        "Q2": [135, 102, 128, 91, 118],
        "Q3": [118, 110, 145, 85, 125],
        "Q4": [142, 98, 133, 97, 130],
    }
)

fig, ax = plt.subplots(figsize=(8, 5))
ax.axis("off")

cell_text = [df.columns.tolist(), *df.values.tolist()]
table = ax.table(cellText=cell_text, loc="center", edges="B")
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.5)

# ── Background: highlight top-two rows (rows 1–2, all 5 cols) ────────────────
mpltablelayers.add_table_multispan_cell(
    table,
    y0x0=(2, 0),
    width=5,
    height=2,
    facecolor="#d5f5e3",  # light green
    zorder=-1,
)

# ── Background: highlight bottom row (row 5, all 5 cols) ─────────────────────
mpltablelayers.add_table_multispan_cell(
    table,
    y0x0=(5, 0),
    width=5,
    height=1,
    facecolor="#fdebd0",  # light orange
    zorder=-1,
)

ax.set_title("Background shading — zorder=-1 keeps text on top", pad=12, fontsize=10)

_ = plt.tight_layout()
