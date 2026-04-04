"""# Foreground overlay

Place a colored rectangle *on top of* table cells using ``add_table_multispan_cell``
with ``zorder=3``.  Values above the table grid (zorder 0–2) cover the cell text
and borders, making this useful for censored or redacted regions.

Use ``set_text_props`` on the returned span to add a replacement label.
"""

# %%
import matplotlib.pyplot as plt
import pandas as pd

import mpltablelayers

df = pd.DataFrame(
    {
        "Employee": ["Alice", "Bob", "Charlie", "Dave", "Eve"],
        "Department": ["Eng", "Sales", "Eng", "HR", "Sales"],
        "Salary": [95000, 72000, 88000, 67000, 78000],
        "Bonus": [12000, 8500, 11000, 6000, 9500],
    }
)

fig, ax = plt.subplots(figsize=(8, 4))
ax.axis("off")

cell_text = [df.columns.tolist(), *df.values.tolist()]
table = ax.table(cellText=cell_text, loc="center", edges="B")
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.5)

# ── Foreground: redact salary + bonus for rows 3–4 ───────────────────────────
redacted = mpltablelayers.add_table_multispan_cell(
    table,
    y0x0=(4, 2),
    width=2,
    height=2,
    facecolor="#1c2833",  # near-black
    zorder=3,
    text="CONFIDENTIAL",
    loc="center",
)
redacted.set_text_props(
    color="white", fontsize=8, weight="bold", ha="center", va="center"
)

ax.set_title("Foreground overlay — zorder=3 covers cell text", pad=12, fontsize=10)

_ = plt.tight_layout()
