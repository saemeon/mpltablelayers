# mpltablelayers

Composable, styled table layers for [matplotlib](https://matplotlib.org/).

**mpltablelayers** fills the biggest gap in the matplotlib table ecosystem:
**spanning/merged cells** and **MultiIndex-aware hierarchical headers** --
features that no existing library (`plottable`, `blume`, built-in `matplotlib.table`) provides.

## Features

- **SpanCell** -- cells that span rectangular regions, dynamically tracking anchor cells
- **Hierarchical headers** -- automatic MultiIndex header construction with per-level and per-label styling
- **Property helpers** -- apply styling at table, row, column, cell, or range level
- Works with any existing `matplotlib.table.Table` -- no special subclass needed

## Install

```bash
pip install mpltablelayers
```

## Quick start

```python
import matplotlib.pyplot as plt
import pandas as pd
import mpltablelayers as mtl

columns = pd.MultiIndex.from_tuples([
    ("Revenue", "Q1"), ("Revenue", "Q2"),
    ("Costs", "Q1"), ("Costs", "Q2"),
])

fig, ax = plt.subplots()
ax.axis("off")

# 2 blank header rows (one per MultiIndex level) + 2 data rows
header_rows = [[""] * 4] * columns.nlevels
data = [["100", "120", "80", "90"], ["110", "130", "85", "95"]]
table = ax.table(
    cellText=header_rows + data,
    cellLoc="right",
    loc="upper left",
)

# Hierarchical header with styled spans
mtl.add_hierarchical_header(
    table, columns,
    default_properties={"facecolor": "lightblue", "text_props": {"weight": "bold"}},
    label_properties={"Costs": {"facecolor": "lightyellow"}},
)

plt.show()
```

## API overview

| Function | Purpose |
|----------|---------|
| `resolve_header_spans()` | Analyze a MultiIndex into span groups |
| `add_hierarchical_header()` | Construct SpanCell-based headers on a table |
| `add_table_multispan_cell()` | Create a single SpanCell by position + size |
| `apply_table_property()` | Style all cells |
| `apply_table_cell_property()` | Style a single cell |
| `apply_table_row_property()` | Style a full row |
| `apply_table_col_property()` | Style a full column |
| `apply_table_range_property()` | Style a rectangular range |

## Documentation

Full docs: [saemeon.github.io/mpltablelayers](https://saemeon.github.io/mpltablelayers/)
