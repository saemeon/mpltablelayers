"""# Circle cell highlight

Draw a circle (or ellipse) around one or more table cells using
``add_table_cell_annotation`` with ``circle=True``.

Set ``fill=True`` and a semi-transparent ``facecolor`` to shade the interior,
or leave the default ``fill=False`` for an outline-only callout.
"""

# %%
import matplotlib.pyplot as plt
import pandas as pd

import mpltablelayers

df = pd.DataFrame(
    {
        "City": ["Berlin", "Paris", "Rome", "Madrid", "Vienna"],
        "Temp °C": [18, 22, 28, 25, 16],
        "Rain mm": [52, 45, 30, 38, 48],
        "Sun hrs": [6.2, 7.1, 9.4, 8.8, 5.9],
    }
)

fig, ax = plt.subplots(figsize=(8, 5))
ax.axis("off")

cell_text = [df.columns.tolist(), *df.values.tolist()]
table = ax.table(cellText=cell_text, loc="center", edges="B")
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.5)

# ── Circle: highlight Rome's sunshine hours (row 3, col 3) ───────────────────
# Row 0 = header, rows 1–5 = data → Rome is row 3
mpltablelayers.add_table_cell_annotation(
    table,
    y0x0=(3, 3),
    circle=True,
    edgecolor="#e67e22",
    linewidth=2.5,
    padding=0.03,
)

# ── Circle spanning two cells: highlight Rome + Madrid temperature ────────────
mpltablelayers.add_table_cell_annotation(
    table,
    y0x0=(4, 1),
    width=1,
    height=2,
    circle=False,  # ellipse — taller than wide
    edgecolor="#2980b9",
    linewidth=2,
    padding=0.03,
    linestyle="--",
)

ax.annotate(
    "Hottest\ncities",
    xy=(1, 0.5),
    xycoords="axes fraction",
    xytext=(1.02, 0.42),
    textcoords="axes fraction",
    fontsize=8,
    color="#2980b9",
    annotation_clip=False,
)

_ = plt.tight_layout()
