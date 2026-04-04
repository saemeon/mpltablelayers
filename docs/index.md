# mpltablelayers

Styled table layers for matplotlib.

**mpltablelayers** provides composable primitives for building publication-quality
tables on top of `matplotlib.table`:

- **SpanCell** -- cells that span rectangular regions, dynamically tracking anchor cells
- **Hierarchical headers** -- automatic MultiIndex-aware header construction with per-span styling
- **Property application** -- consistent styling at the table, row, column, cell, or range level

## Installation

```bash
pip install mpltablelayers
```

## Quick start

```python
import matplotlib.pyplot as plt
import pandas as pd
import mpltablelayers as mtl

# Create a MultiIndex
columns = pd.MultiIndex.from_tuples([
    ("Revenue", "Q1"), ("Revenue", "Q2"),
    ("Costs", "Q1"), ("Costs", "Q2"),
])

# Build a table with blank header rows + data rows
fig, ax = plt.subplots()
ax.axis("off")

header_rows = [[""] * 4] * columns.nlevels  # one row per level
data = [["100", "120", "80", "90"], ["110", "130", "85", "95"]]
table = ax.table(
    cellText=header_rows + data,
    cellLoc="right",
    loc="upper left",
)

# Add hierarchical header with styled spans
mtl.add_hierarchical_header(
    table, columns,
    default_properties={"facecolor": "lightblue", "text_props": {"weight": "bold"}},
    label_properties={"Costs": {"facecolor": "lightyellow"}},
)

# Style the body
mtl.apply_table_property(table, {"text_props": {"ha": "right"}})

plt.show()
```

## Key concepts

### SpanCell

A `SpanCell` overlays a rectangular region of existing table cells.  It
automatically updates its position and size when the underlying anchor cells
move -- no manual bookkeeping needed.

```python
span = mtl.add_table_multispan_cell(table, (2, 0), width=3, height=1, text="Total")
span.set_facecolor("lightgrey")
```

### Header span resolution

`resolve_header_spans` analyzes a `pd.MultiIndex` and returns `HeaderSpan`
objects describing which columns should be merged at each level:

```python
spans, n_levels = mtl.resolve_header_spans(columns)
for s in spans:
    print(f"Level {s.level}: '{s.label}' cols {s.start_col}-{s.end_col}")
```

### Property dictionaries

All `apply_table_*` functions accept a property dictionary:

| Key | Effect |
|-----|--------|
| `text_props` | Forwarded to `cell.set_text_props(**text_props)` |
| `pad` | Sets `cell.PAD` |
| `height_scaling` | Multiplies current cell height |
| `visible_edges` | Sets `cell.visible_edges` |
| `custom_modifiers` | List of callables invoked with the cell |
| Any other key | Forwarded to `cell.set(**kwargs)` |
