"""Compatibility helpers for `plottable <https://github.com/znstrider/plottable>`_ tables.

plottable cells are positioned once at construction time and expose no
``set_x`` / ``set_y`` methods, so the interceptor-based :class:`SpanCell`
pattern used for matplotlib and blume tables does not apply.  The helpers in
this module read cell positions directly from plottable's cell objects and add
plain :class:`matplotlib.patches.Rectangle` overlays to the axes instead.

Coordinate conventions
----------------------
plottable uses a (col, row) data-coordinate system where:

- ``x`` increases left-to-right starting at 0, stepping by column width.
- ``y`` equals the 0-based row index (row 0 → y=0, row 1 → y=1, …).
- The y-axis is inverted (``ax.invert_yaxis()`` is called after construction),
  so row 0 appears at the **top** of the table.

Row and column indices passed to the helpers in this module follow the same
0-based, top-to-bottom, left-to-right convention as plottable's ``Table.cells``
dictionary.  Pass ``row=-1`` to target the column-label header row.
"""

from __future__ import annotations

from matplotlib.patches import Rectangle

__all__ = ["add_plottable_multispan_cell"]


def add_plottable_multispan_cell(
    tab,
    row: int,
    col: int,
    width: int,
    height: int,
    facecolor: str = "lightgrey",
    zorder: int | float = 2,
    linewidth: float = 0,
    **kwargs,
) -> Rectangle:
    """Add a shaded :class:`~matplotlib.patches.Rectangle` over a region of a
    plottable table.

    Parameters
    ----------
    tab : plottable.Table
        The plottable table to shade.
    row : int
        Top row of the region (0-indexed; 0 = first data row).
        Pass ``-1`` to target the column-label header row.
    col : int
        Left column of the region (0-indexed).
    width : int
        Number of columns to span rightward.
    height : int
        Number of rows to span downward.
    facecolor : str or tuple, default "lightgrey"
        Background colour of the rectangle.
    zorder : float, default 2
        Drawing order. 2 renders on top of plottable's default cell patches
        (zorder 1), so the shading is visible.
    linewidth : float, default 0
        Border line width.
    **kwargs
        Additional keyword arguments forwarded to
        :class:`matplotlib.patches.Rectangle`.

    Returns
    -------
    matplotlib.patches.Rectangle
        The created patch, already added to ``tab.ax``.

    Notes
    -----
    Because plottable cells are positioned at construction time and never
    repositioned, this function must be called **after** ``plottable.Table``
    has been fully constructed.
    """

    def _get_cell(r, c):
        if r == -1:
            label_cells = {cell.col_idx: cell for cell in tab.col_label_row.cells}
            return label_cells[c]
        return tab.cells[(r, c)]

    cell_tl = _get_cell(row, col)
    cell_br = _get_cell(row + height - 1, col + width - 1)

    x = cell_tl.x
    y = cell_tl.y
    w = cell_br.x + cell_br.width - x
    h = cell_br.y + cell_br.height - y

    rect = Rectangle(
        (x, y),
        w,
        h,
        facecolor=facecolor,
        zorder=zorder,
        linewidth=linewidth,
        **kwargs,
    )
    tab.ax.add_patch(rect)
    return rect
