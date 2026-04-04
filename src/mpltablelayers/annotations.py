"""Cell annotation overlays — circles and ellipses drawn around table cells.

Unlike :class:`~mpltablelayers.SpanCell`, which fills a rectangular region,
the annotations in this module draw an *outline* (by default unfilled)
:class:`~matplotlib.patches.Ellipse` around one or more cells.  The ellipse
can extend beyond the table boundaries, making it useful for calling out
individual cells or groups of cells with an annotation that sits visually
*outside* the table grid.

For text labels, use a standard matplotlib call after receiving the patch::

    ann = add_table_cell_annotation(table, y0x0=(3, 2))
    # place a label outside the ellipse using axes annotation
    ax.annotate("Note!", xy=(0.5, 0.5), xycoords=ann,
                xytext=(10, 10), textcoords="offset points",
                arrowprops=dict(arrowstyle="->"))
"""

from __future__ import annotations

from matplotlib.patches import Ellipse

from .interceptor_registry import register_method_interceptor

__all__ = [
    "CellEllipse",
    "add_table_cell_annotation",
    "add_table_arrow_annotation",
    "add_plottable_cell_annotation",
]


class CellEllipse(Ellipse):
    """An :class:`~matplotlib.patches.Ellipse` drawn around one or more
    matplotlib / blume table cells.

    Like :class:`~mpltablelayers.SpanCell`, ``CellEllipse`` registers
    interceptors on the anchor cells so the ellipse follows the table layout
    automatically whenever the table is redrawn or resized.

    Parameters
    ----------
    table : matplotlib.table.Table or blume.table.Table
        The table containing the anchor cells.
    cell_x0y0 : Cell
        Anchor cell defining the bottom-left corner of the spanned region.
    cell_x1y1 : Cell
        Anchor cell defining the upper-right corner of the spanned region.
    padding : float, default 0.1
        Extra space added around the cell bounds on every side, expressed in
        the same units as the table's internal coordinate system.
    **kwargs
        Forwarded to :class:`~matplotlib.patches.Ellipse`.  Useful keys:
        ``edgecolor``, ``linewidth``, ``linestyle``, ``fill``, ``zorder``.
    """

    def __init__(
        self,
        table,
        cell_x0y0,
        cell_x1y1,
        padding: float = 0.1,
        circle: bool = False,
        **kwargs,
    ) -> None:
        super().__init__((0, 0), 1, 1, **kwargs)

        self._cell_x0y0 = cell_x0y0
        self._cell_x1y1 = cell_x1y1
        self._table = table
        self._padding = padding
        self._circle = circle

        self.set_figure(table.get_figure())
        self.set_transform(table.get_transform())
        table.get_figure().add_artist(self)

        register_method_interceptor(cell_x0y0.set_x, self.update_bounds)
        register_method_interceptor(cell_x0y0.set_y, self.update_bounds)
        register_method_interceptor(cell_x1y1.set_x, self.update_bounds)
        register_method_interceptor(cell_x1y1.set_width, self.update_bounds)
        register_method_interceptor(cell_x1y1.set_y, self.update_bounds)
        register_method_interceptor(cell_x1y1.set_height, self.update_bounds)
        register_method_interceptor(
            cell_x0y0.set_figure, self.set_figure, pass_args=True, pass_kwargs=True
        )
        register_method_interceptor(
            cell_x0y0.set_transform,
            self.set_transform,
            pass_args=True,
            pass_kwargs=True,
        )

    def update_bounds(self) -> None:
        """Recompute the ellipse centre and axes from the anchor cells."""
        x0 = self._cell_x0y0.get_x()
        x1 = self._cell_x1y1.get_x() + self._cell_x1y1.get_width()
        y0 = self._cell_x0y0.get_y()
        y1 = self._cell_x1y1.get_y() + self._cell_x1y1.get_height()
        if None not in (x0, y0, x1, y1):
            self.set_center(((x0 + x1) / 2, (y0 + y1) / 2))
            w = (x1 - x0) + 2 * self._padding
            h = (y1 - y0) + 2 * self._padding
            if self._circle:
                w = h = max(w, h)
            self.set_width(w)
            self.set_height(h)


def add_table_cell_annotation(
    table,
    y0x0: tuple[int, int],
    width: int = 1,
    height: int = 1,
    padding: float = 0.1,
    circle: bool = False,
    fill: bool = False,
    edgecolor: str = "red",
    linewidth: float = 2,
    linestyle: str = "-",
    zorder: int | float = 4,
    **kwargs,
) -> CellEllipse:
    """Draw a :class:`CellEllipse` around a region of a matplotlib / blume table.

    Parameters
    ----------
    table : matplotlib.table.Table or blume.table.Table
    y0x0 : tuple[int, int]
        ``(row, col)`` of the bottom-left anchor cell.  Uses the same
        indexing convention as :func:`~mpltablelayers.add_table_multispan_cell`:
        row 0 is the first rendered row (header), columns are 0-based.
    width : int, default 1
        Number of columns to span rightward.
    height : int, default 1
        Number of rows to span upward.
    padding : float, default 0.1
        Extra space outside the cell bounds, in table data units.
    fill : bool, default False
        Whether to fill the ellipse interior.
    edgecolor : str, default "red"
        Ellipse border colour.
    linewidth : float, default 2
        Ellipse border width.
    linestyle : str, default "-"
        Ellipse border line style.
    zorder : float, default 4
        Drawing order; 4 places the annotation on top of everything.
    **kwargs
        Additional keyword arguments forwarded to :class:`CellEllipse` /
        :class:`~matplotlib.patches.Ellipse`.

    Returns
    -------
    CellEllipse
        The annotation patch, already added to the figure.
    """
    (y0, x0) = y0x0
    (y1, x1) = (y0 - height + 1, x0 + width - 1)
    cell_x0y0 = table.get_celld()[(y0, x0)]
    cell_x1y1 = table.get_celld()[(y1, x1)]
    return CellEllipse(
        table,
        cell_x0y0,
        cell_x1y1,
        padding=padding,
        circle=circle,
        fill=fill,
        edgecolor=edgecolor,
        linewidth=linewidth,
        linestyle=linestyle,
        zorder=zorder,
        **kwargs,
    )


def add_plottable_cell_annotation(
    tab,
    row: int,
    col: int,
    width: int = 1,
    height: int = 1,
    padding: float = 0.1,
    circle: bool = False,
    fill: bool = False,
    edgecolor: str = "red",
    linewidth: float = 2,
    linestyle: str = "-",
    zorder: int | float = 4,
    **kwargs,
) -> Ellipse:
    """Draw an :class:`~matplotlib.patches.Ellipse` around a region of a
    plottable table.

    plottable cells are positioned at construction time, so the ellipse is
    computed immediately (no interceptors needed).

    Parameters
    ----------
    tab : plottable.Table
    row : int
        Top row of the region (0-indexed; ``-1`` = column-label header row).
    col : int
        Left column of the region (0-indexed).
    width : int, default 1
        Number of columns to span rightward.
    height : int, default 1
        Number of rows to span downward.
    padding : float, default 0.1
        Extra space outside the cell bounds, in plottable data units.
    fill : bool, default False
        Whether to fill the ellipse interior.
    edgecolor : str, default "red"
        Ellipse border colour.
    linewidth : float, default 2
        Ellipse border width.
    linestyle : str, default "-"
        Ellipse border line style.
    zorder : float, default 4
        Drawing order.
    **kwargs
        Additional keyword arguments forwarded to
        :class:`~matplotlib.patches.Ellipse`.

    Returns
    -------
    matplotlib.patches.Ellipse
        The annotation patch, already added to ``tab.ax``.
    """

    def _get_cell(r, c):
        if r == -1:
            label_cells = {cell.col_idx: cell for cell in tab.col_label_row.cells}
            return label_cells[c]
        return tab.cells[(r, c)]

    cell_tl = _get_cell(row, col)
    cell_br = _get_cell(row + height - 1, col + width - 1)

    x0, y0 = cell_tl.x, cell_tl.y
    x1 = cell_br.x + cell_br.width
    y1 = cell_br.y + cell_br.height

    w = (x1 - x0) + 2 * padding
    h = (y1 - y0) + 2 * padding
    if circle:
        w = h = max(w, h)

    ell = Ellipse(
        ((x0 + x1) / 2, (y0 + y1) / 2),
        width=w,
        height=h,
        fill=fill,
        edgecolor=edgecolor,
        linewidth=linewidth,
        linestyle=linestyle,
        zorder=zorder,
        **kwargs,
    )
    tab.ax.add_patch(ell)
    return ell


def add_table_arrow_annotation(
    table,
    ax,
    y0x0: tuple[int, int],
    label: str,
    xytext: tuple[float, float],
    width: int = 1,
    height: int = 1,
    padding: float = 0.1,
    circle: bool = False,
    edgecolor: str = "red",
    linewidth: float = 2,
    arrowprops: dict | None = None,
    annotation_kwargs: dict | None = None,
    **kwargs,
) -> tuple[CellEllipse, object]:
    """Draw a :class:`CellEllipse` around a cell and attach an arrow annotation.

    Combines :func:`add_table_cell_annotation` with a standard
    :meth:`~matplotlib.axes.Axes.annotate` call so the arrow originates from
    the ellipse and points to the cell.

    Parameters
    ----------
    table : matplotlib.table.Table or blume.table.Table
    ax : matplotlib.axes.Axes
        The axes that owns the table (needed for ``ax.annotate``).
    y0x0 : tuple[int, int]
        ``(row, col)`` of the bottom-left anchor cell.
    label : str
        Text label placed at the tail of the arrow.
    xytext : tuple[float, float]
        Position of the label in *axes fraction* coordinates
        ``(x, y)`` where ``(0, 0)`` is the bottom-left and ``(1, 1)``
        the top-right of the axes.
    width : int, default 1
        Number of columns spanned by the ellipse.
    height : int, default 1
        Number of rows spanned by the ellipse.
    padding : float, default 0.1
        Extra space outside the cell bounds for the ellipse.
    circle : bool, default False
        Force the ellipse to be a circle.
    edgecolor : str, default "red"
        Colour of the ellipse edge and arrow.
    linewidth : float, default 2
        Line width of the ellipse edge.
    arrowprops : dict, optional
        Passed directly to :meth:`~matplotlib.axes.Axes.annotate`.
        Defaults to ``{"arrowstyle": "->", "color": edgecolor, "lw": 1.5}``.
    annotation_kwargs : dict, optional
        Extra keyword arguments forwarded to
        :meth:`~matplotlib.axes.Axes.annotate` (e.g. ``fontsize``, ``color``).
    **kwargs
        Additional keyword arguments forwarded to :class:`CellEllipse` /
        :class:`~matplotlib.patches.Ellipse`.

    Returns
    -------
    ellipse : CellEllipse
        The ellipse patch, already added to the figure.
    annotation : matplotlib.text.Annotation
        The annotation artist, already added to the axes.
    """
    if arrowprops is None:
        arrowprops = {"arrowstyle": "->", "color": edgecolor, "lw": 1.5}
    if annotation_kwargs is None:
        annotation_kwargs = {}

    ellipse = add_table_cell_annotation(
        table,
        y0x0=y0x0,
        width=width,
        height=height,
        padding=padding,
        circle=circle,
        edgecolor=edgecolor,
        linewidth=linewidth,
        **kwargs,
    )
    annotation = ax.annotate(
        label,
        xy=(0.5, 0.5),
        xycoords=ellipse,
        xytext=xytext,
        textcoords="axes fraction",
        arrowprops=arrowprops,
        annotation_clip=False,
        **annotation_kwargs,
    )
    return ellipse, annotation
