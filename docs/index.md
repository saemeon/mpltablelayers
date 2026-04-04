# mpltablelayers

**mpltablelayers** adds styled overlay layers on top of
[matplotlib](https://matplotlib.org/stable/api/table_api.html),
[blume](https://github.com/swfiua/blume), and
[plottable](https://github.com/znstrider/plottable) tables.

## Features

- **Background / Foreground shading** — color rectangular regions behind or in front of cells
- **Span text** — text labels that span multiple columns or rows
- **LaTeX cells** — math-mode content rendered with MathJax or `usetex`
- **Arrow annotations** — arrows pointing to individual cells with labels
- **Circle / ellipse highlights** — outline a cell or a group of cells

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

See the [Examples](generated/gallery) gallery for focused demonstrations of each feature.
