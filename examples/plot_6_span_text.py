"""# Span text

Add a text label that spans multiple columns or rows using
``add_table_multispan_cell`` with a ``text`` argument.

Common use cases are multi-level headers (a group label above several columns)
and section dividers (a full-width label between data rows).
"""

# %%
import matplotlib.pyplot as plt
import pandas as pd

import mpltablelayers

df = pd.DataFrame(
    {
        "Name": ["Alice", "Bob", "Charlie", "Dave"],
        "Math": [85, 92, 78, 95],
        "Science": [90, 85, 82, 88],
        "History": [78, 88, 91, 72],
        "Art": [91, 76, 84, 80],
    }
)

fig, ax = plt.subplots(figsize=(8, 5))
ax.axis("off")

# Row 0: group header; row 1: column labels; rows 2–5: data
cell_text = [
    [""] * 5,  # placeholder — will be replaced by span
    df.columns.tolist(),
    *df.values.tolist(),
]
table = ax.table(cellText=cell_text, loc="center", edges="B")
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.5)

# ── Span text: full-width title header (row 0) ───────────────────────────────
for c in range(5):
    table.get_celld()[(0, c)].set_visible_edges("")

title = mpltablelayers.add_table_multispan_cell(
    table,
    y0x0=(0, 0),
    width=5,
    height=1,
    facecolor="#2c3e50",
    zorder=3,
    text="Academic Results — Spring Semester",
    loc="center",
)
title.set_text_props(
    color="white", weight="bold", fontsize=11, ha="center", va="center"
)

# ── Span text: "Subjects" sub-header spanning cols 1–4 (row 1) ───────────────
for c in range(1, 5):
    table.get_celld()[(1, c)].get_text().set_text("")
    table.get_celld()[(1, c)].set_visible_edges("")

subjects = mpltablelayers.add_table_multispan_cell(
    table,
    y0x0=(1, 1),
    width=4,
    height=1,
    facecolor="#2980b9",
    zorder=3,
    text="Subjects",
    loc="center",
)
subjects.set_text_props(
    color="white", weight="bold", fontsize=9, ha="center", va="center"
)

_ = plt.tight_layout()
