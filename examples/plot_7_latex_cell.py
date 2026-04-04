"""# LaTeX cell content

Render mathematical expressions inside table cells using matplotlib's mathtext
renderer (no external LaTeX installation required).

Wrap any cell text in ``$...$`` to activate mathtext.  For more complex
expressions, enable ``plt.rcParams["text.usetex"] = True`` (requires a working
LaTeX distribution).
"""

# %%
import matplotlib.pyplot as plt

import mpltablelayers

# Use matplotlib's built-in mathtext — no external LaTeX needed
cell_text = [
    ["Formula", "Rendered"],
    [r"$E = mc^2$", "Energy–mass equivalence"],
    [r"$\sigma = \sqrt{\frac{1}{N}\sum_{i}(x_i - \mu)^2}$", "Standard deviation"],
    [r"$F = G\,\frac{m_1 m_2}{r^2}$", "Newton's law of gravitation"],
    [r"$\nabla \cdot \mathbf{E} = \frac{\rho}{\varepsilon_0}$", "Gauss's law"],
]

fig, ax = plt.subplots(figsize=(8, 4))
ax.axis("off")

table = ax.table(cellText=cell_text, loc="center", edges="B")
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2.2)

# ── Header styling ────────────────────────────────────────────────────────────
mpltablelayers.apply_table_row_property(
    table,
    0,
    {"facecolor": "#2c3e50", "text_props": {"color": "white", "weight": "bold"}},
)

# ── Alternating row shading ───────────────────────────────────────────────────
for row in range(1, 5, 2):
    mpltablelayers.apply_table_row_property(table, row, {"facecolor": "#eaf2ff"})

ax.set_title("LaTeX / mathtext in table cells", pad=12, fontsize=10)

_ = plt.tight_layout()
