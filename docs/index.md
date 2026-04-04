# mpltablelayers

**mpltablelayers** adds styled overlay layers on top of
[matplotlib](https://matplotlib.org/stable/api/table_api.html),
[blume](https://github.com/swfiua/blume), and
[plottable](https://github.com/znstrider/plottable) tables.

## Features

- **Background / Foreground shading** -- color rectangular regions behind or in front of cells
- **Span text** -- text labels that span multiple columns or rows
- **Hierarchical headers** -- automatic MultiIndex-aware header construction with per-span styling
- **LaTeX cells** -- math-mode content rendered with MathJax or `usetex`
- **Arrow annotations** -- arrows pointing to individual cells with labels
- **Circle / ellipse highlights** -- outline a cell or a group of cells
- **Property application** -- consistent styling at the table, row, column, cell, or range level

## Installation

```bash
pip install mpltablelayers
```

## Quickstart

```python
import matplotlib.pyplot as plt
import pandas as pd
import mpltablelayers

df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})

fig, ax = plt.subplots(figsize=(4, 2))
ax.axis("off")
table = ax.table(cellText=df.values.tolist(), colLabels=df.columns.tolist(), loc="center")

# shade the first data row
mpltablelayers.add_table_multispan_cell(table, y0x0=(1, 0), width=2, height=1, facecolor="#d4e6f1")
plt.tight_layout()
plt.show()
```

## Hierarchical headers

`resolve_header_spans` analyzes a `pd.MultiIndex` and returns `HeaderSpan`
objects describing which columns should be merged at each level.
`add_hierarchical_header` creates styled `SpanCell` overlays from those spans:

```python
import mpltablelayers as mtl

columns = pd.MultiIndex.from_tuples([
    ("Revenue", "Q1"), ("Revenue", "Q2"),
    ("Costs", "Q1"), ("Costs", "Q2"),
])

fig, ax = plt.subplots()
ax.axis("off")

header_rows = [[""] * 4] * columns.nlevels
data = [["100", "120", "80", "90"], ["110", "130", "85", "95"]]
table = ax.table(cellText=header_rows + data, cellLoc="right", loc="upper left")

mtl.add_hierarchical_header(
    table, columns,
    default_properties={"facecolor": "lightblue", "text_props": {"weight": "bold"}},
    label_properties={"Costs": {"facecolor": "lightyellow"}},
)
plt.show()
```

## Property dictionaries

All `apply_table_*` functions accept a property dictionary:

| Key | Effect |
|-----|--------|
| `text_props` | Forwarded to `cell.set_text_props(**text_props)` |
| `pad` | Sets `cell.PAD` |
| `height_scaling` | Multiplies current cell height |
| `visible_edges` | Sets `cell.visible_edges` |
| `custom_modifiers` | List of callables invoked with the cell |
| Any other key | Forwarded to `cell.set(**kwargs)` |

See the [Examples](generated/gallery) gallery for focused demonstrations of each feature.
