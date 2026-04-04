"""# Shading, censoring, header spans, and annotations on a matplotlib table

Four overlay layers using ``add_table_multispan_cell`` and
``add_table_cell_annotation``:

- light blue **background shading** over a group of rows
- black **censored region** with diagonal text
- **two-level spanning header**: full-width title row + Scores sub-header
- **ellipse annotation** calling out a single outstanding cell
"""

# %%
import matplotlib.pyplot as plt
import pandas as pd

from mpltablelayers import add_table_cell_annotation, add_table_multispan_cell

df = pd.DataFrame(
    {
        "Name": ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank", "Grace", "Henry"],
        "Math": [85, 92, 78, 95, 88, 73, 91, 67],
        "Science": [90, 85, 82, 88, 79, 95, 84, 76],
        "English": [78, 88, 91, 72, 94, 81, 86, 90],
        "Grade": ["B", "A", "B", "A", "B", "B", "A", "C"],
    }
)

fig, ax = plt.subplots(figsize=(7, 5))
ax.axis("off")

# Embed two header rows in cellText so both levels can host SpanCells.
# Row 0 = title, row 1 = column labels, rows 2–9 = data.
cell_text = [
    ["Student Performance"] + [""] * 4,
    df.columns.tolist(),
    *df.values.tolist(),
]
table = ax.table(cellText=cell_text, loc="center", edges="B")
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.5)

# ── Layer 1: background shading ──────────────────────────────────────────────
# light blue over Group A (data rows 2–5, all 5 cols)
add_table_multispan_cell(
    table, y0x0=(5, 0), width=5, height=4, facecolor="#d4e6f1", zorder=-1
)

# ── Layer 2: censored region ─────────────────────────────────────────────────
# black out data rows 6–7, score cols 1–3, with diagonal "REDACTED" text
censor = add_table_multispan_cell(
    table,
    y0x0=(7, 1),
    width=3,
    height=2,
    facecolor="black",
    zorder=3,
    text="REDACTED",
    loc="center",
)
censor.set_text_props(
    color="white", rotation=30, ha="center", va="center", fontsize=8, weight="bold"
)

# ── Layer 3a: full-width title header (row 0, all 5 cols) ────────────────────
for c in range(5):
    hcell = table.get_celld()[(0, c)]
    hcell.get_text().set_text("")
    hcell.visible_edges = ""
    hcell.set_facecolor("#1a5276")

title = add_table_multispan_cell(
    table,
    y0x0=(0, 0),
    width=5,
    height=1,
    facecolor="#1a5276",
    zorder=3,
    text="Student Performance",
    loc="center",
)
title.set_text_props(
    color="white", ha="center", va="center", weight="bold", fontsize=11
)


# ── Layer 3b: "Scores" sub-header (row 1, cols 1–3) ─────────────────────────
for c in [1, 2, 3]:
    hcell = table.get_celld()[(1, c)]
    hcell.get_text().set_text("")
    hcell.visible_edges = ""
    hcell.set_facecolor("#2980b9")

scores_hdr = add_table_multispan_cell(
    table,
    y0x0=(1, 1),
    width=3,
    height=1,
    facecolor="#2980b9",
    zorder=3,
    text="Scores",
    loc="center",
)
scores_hdr.set_text_props(
    color="white", ha="center", va="center", weight="bold", fontsize=9
)

# ── Layer 4: ellipse annotation calling out Dave's Math score (95) ───────────
# Row 0=title, row 1=col labels, rows 2–9=data → Dave is row 5, Math is col 1
ann = add_table_cell_annotation(
    table, y0x0=(5, 1), edgecolor="#c0392b", linewidth=2.5, padding=0
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
