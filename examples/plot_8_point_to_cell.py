"""# Point to cell

Draw an arrow from a text label to a specific table cell using
``add_table_arrow_annotation``.

The function wraps ``add_table_cell_annotation`` (which creates the
:class:`~mpltablelayers.CellEllipse` anchor) and ``ax.annotate`` in a single
call.  The ellipse acts as the ``xycoords`` reference so the arrow always
points to the correct cell even after the table is resized.
"""

# %%
import matplotlib.pyplot as plt
import pandas as pd

import mpltablelayers

df = pd.DataFrame(
    {
        "Name": ["Alice", "Bob", "Charlie", "Dave", "Eve"],
        "Math": [85, 92, 78, 95, 88],
        "Science": [90, 85, 82, 88, 79],
        "English": [78, 88, 91, 72, 94],
    }
)

fig, ax = plt.subplots(figsize=(8, 5))
ax.axis("off")

cell_text = [df.columns.tolist(), *df.values.tolist()]
table = ax.table(cellText=cell_text, loc="center", edges="B")
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.5)

# ── Arrow annotation: highlight Dave's top Math score (row 4, col 1) ─────────
# Row 0 = header, rows 1–5 = data → Dave is row 4
mpltablelayers.add_table_arrow_annotation(
    table,
    ax,
    y0x0=(4, 1),
    label="Top score!",
    xytext=(0.82, 0.62),
    edgecolor="#c0392b",
    linewidth=2,
    padding=0.02,
    annotation_kwargs={"fontsize": 9, "color": "#c0392b", "weight": "bold"},
    arrowprops={
        "arrowstyle": "->",
        "color": "#c0392b",
        "lw": 1.5,
        "connectionstyle": "arc3,rad=0.3",
    },
)

# ── Arrow annotation: highlight Eve's top English score (row 5, col 3) ───────
mpltablelayers.add_table_arrow_annotation(
    table,
    ax,
    y0x0=(5, 3),
    label="Best in\nEnglish",
    xytext=(0.85, 0.25),
    edgecolor="#1a5276",
    linewidth=2,
    padding=0.02,
    annotation_kwargs={"fontsize": 9, "color": "#1a5276", "weight": "bold"},
    arrowprops={
        "arrowstyle": "->",
        "color": "#1a5276",
        "lw": 1.5,
        "connectionstyle": "arc3,rad=-0.3",
    },
)

_ = plt.tight_layout()
