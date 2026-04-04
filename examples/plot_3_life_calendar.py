"""# Life Calendar

Visualise a 80-year human lifespan as a 52 × 80 grid: fifty-two columns for the
weeks within a year, eighty rows for years 0–79.

Lived weeks are shaded; the current week is circled with an annotated arrow
pointing outside the table.

The example uses a birth year of 1990 and a current year of 2026 (week 11).
"""

# %%
import datetime

import matplotlib.pyplot as plt

from mpltablelayers import add_table_cell_annotation, add_table_multispan_cell

BIRTH_YEAR = 1990
CURRENT_YEAR = 2026
WEEKS_PER_YEAR = 52
N_YEARS = 80

birth_date = datetime.date(BIRTH_YEAR, 1, 1)
current_date = datetime.date(CURRENT_YEAR, 1, 1)
age_in_weeks = (current_date - birth_date).days // 7

current_week_in_year = current_date.isocalendar()[1]

full_years = age_in_weeks // WEEKS_PER_YEAR
week_in_year = age_in_weeks % WEEKS_PER_YEAR

col_labels = [str(w) for w in range(1, WEEKS_PER_YEAR + 1)]
row_labels = [str(y) for y in range(N_YEARS)]

cell_text = [
    ["Life Calendar"] + [""] * WEEKS_PER_YEAR,
    [""] + col_labels,
    *[[lbl] + [""] * WEEKS_PER_YEAR for lbl in row_labels],
]

fig, ax = plt.subplots(figsize=(7, 7))
ax.axis("off")

table = ax.table(cellText=cell_text, loc="center", edges="B")
table.auto_set_font_size(False)
table.set_fontsize(4)
table.scale(0.8, 0.5)

for c in range(WEEKS_PER_YEAR + 1):
    cell = table.get_celld()[(0, c)]
    cell.get_text().set_text("")
    cell.visible_edges = ""
    cell.set_facecolor("#2c3e50")

title = add_table_multispan_cell(
    table,
    y0x0=(0, 1),
    width=WEEKS_PER_YEAR,
    height=1,
    facecolor="#2c3e50",
    zorder=3,
    text="Life Calendar  ·  Born 1990  ·  80 years × 52 weeks",
    loc="center",
)
title.set_text_props(color="white", ha="center", va="center", weight="bold", fontsize=8)

if full_years > 0:
    add_table_multispan_cell(
        table,
        y0x0=(1 + full_years, 1),
        width=WEEKS_PER_YEAR,
        height=full_years,
        facecolor="#2980b9",
        zorder=-1,
    )

if week_in_year > 0:
    add_table_multispan_cell(
        table,
        y0x0=(2 + full_years, 1),
        width=week_in_year,
        height=1,
        facecolor="#2980b9",
        zorder=-1,
    )

ann = add_table_cell_annotation(
    table,
    y0x0=(2 + full_years, 1 + week_in_year),
    edgecolor="#c0392b",
    linewidth=2,
    padding=0,
)
ax.annotate(
    f"Week {current_week_in_year}",
    xy=(1, 0.5),
    xycoords=ann,
    xytext=(1.02, 0.5),
    textcoords="axes fraction",
    color="#c0392b",
    fontsize=6,
    weight="bold",
    annotation_clip=False,
    arrowprops=dict(
        arrowstyle="->", color="#c0392b", lw=1, connectionstyle="arc3,rad=0.3"
    ),
)

_ = plt.tight_layout()

# %%
import matplotlib.pyplot as plt
import pandas as pd

dates = pd.bdate_range(start="2020-01-01", end="2020-01-14", freq="C")
data = pd.DataFrame({"Value": range(len(dates))}, index=dates)
plt.figure(figsize=(10, 5))
plt.plot(data.index, data["Value"])
plt.show()
