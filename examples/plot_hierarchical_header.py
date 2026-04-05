"""
Hierarchical Header
===================

Build a table with a two-level MultiIndex header where each
top-level group is rendered as a styled SpanCell.
"""

import matplotlib.pyplot as plt
import pandas as pd

import mpltablelayers as mtl

# %%
# Define a MultiIndex with two groups

columns = pd.MultiIndex.from_tuples(
    [
        ("Revenue", "Q1"),
        ("Revenue", "Q2"),
        ("Costs", "Q1"),
        ("Costs", "Q2"),
    ]
)

data = [
    ["100", "120", "80", "90"],
    ["110", "130", "85", "95"],
]

# %%
# Create the table and add a hierarchical header

fig, ax = plt.subplots(figsize=(6, 2))
ax.axis("off")

table = ax.table(
    cellText=[[""] * 4] * 2 + data,  # 2 header rows + 2 data rows
    cellLoc="right",
    loc="upper left",
    edges="B",
)
table.auto_set_font_size(False)
table.scale(1, 1.4)

spans = mtl.add_hierarchical_header(
    table,
    columns,
    default_properties={
        "facecolor": "lightblue",
        "text_props": {"weight": "bold", "ha": "left"},
    },
    label_properties={
        "Costs": {"facecolor": "lightyellow"},
    },
)

plt.tight_layout()
plt.show()
