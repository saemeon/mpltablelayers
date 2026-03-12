"""Helpers to plot nice tables.

See Also
--------
- [Matplotlib Table API](https://matplotlib.org/stable/api/table_api.html#matplotlib.table.table)
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import Any, TypeAlias

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.table import Cell, Table

from .interceptor_registry import register_method_interceptor
from .utils import get_text_bbox, requires_usetex, separate_kwargs

__all__ = [
    "make_table",
    "add_table_multispan_cell",
    "apply_table_cell_property",
    "apply_table_col_property",
    "apply_table_range_property",
    "apply_table_row_property",
    "SpanCell",
]

_logger = logging.getLogger(__name__)

IndexLike: TypeAlias = pd.Index | pd.MultiIndex
row: TypeAlias = int | str | IndexLike
col: TypeAlias = int | str | IndexLike
row_col: TypeAlias = tuple[row, col]
width: TypeAlias = int
height: TypeAlias = int
PropertyDict: TypeAlias = dict
TablePropertyDict: TypeAlias = dict

_IndexLikeType = (pd.Index, pd.MultiIndex)
"""
Index like types which we want to support for row/col referencing. We expect them
to provide a `to_list()` method.
"""


linewidth =1
linewidth_bottom =1


class SpanCell(Cell):
    """A table cell that spans a rectangular region defined by two anchor cells.

    `SpanCell` derives its position and size from two existing table cells:
    - `cell_x0y0` defines the top-left corner of the spanned region.
    - `cell_x1y1` defines the bottom-right corner of the spanned region.

    The span cell dynamically tracks changes of the anchor cells. Whenever
    either anchor cell changes its position or size, the span cell updates
    its own bounds accordingly via registered method interceptors.

    `SpanCell` instances can be modified exactly like normal `Cell`
    instances. For example, to control whether the span cell is rendered
    in the background or foreground relative to other cells, adjust its
    drawing order using `spancell.set_zorder()`.

    Parameters
    ----------
    table : Table
        The table to which this spanning cell belongs.
    cell_x0y0 : Cell
        The anchor cell defining the bottom-left corner of the span.
    cell_x1y1 : Cell
        The anchor cell defining the upper-right corner of the span.
    *args
        Positional arguments forwarded to `Cell`.
    **kwargs
        Keyword arguments forwarded to `Cell`.

    Notes
    -----
    The span cell does not replace the anchor cells. It overlays the
    rectangular area between them and must be managed accordingly
    in rendering or layout logic.
    """

    def __init__(self, table: Table, cell_x0y0: Cell, cell_x1y1: Cell, *args, **kwargs):
        super().__init__((0, 0), 1, 1, *args, **kwargs)

        self._cell_x0y0 = cell_x0y0
        self._cell_x1y1 = cell_x1y1
        self._table = table

        self.set_figure(table.get_figure())
        self.set_transform(table.get_transform())
        self._table.get_figure().add_artist(self)

        # Register interceptors on all relevant anchor-cell-methods required to track the moving of the anchor cells
        register_method_interceptor(self._cell_x0y0.set_x, self.update_bounds)
        register_method_interceptor(self._cell_x0y0.set_y, self.update_bounds)
        register_method_interceptor(self._cell_x1y1.set_x, self.update_bounds)
        register_method_interceptor(self._cell_x1y1.set_width, self.update_bounds)
        register_method_interceptor(self._cell_x1y1.set_y, self.update_bounds)
        register_method_interceptor(self._cell_x1y1.set_height, self.update_bounds)
        register_method_interceptor(self._cell_x0y0.set_figure, self.set_figure, pass_args=True, pass_kwargs=True)
        register_method_interceptor(self._cell_x0y0.set_transform, self.set_transform, pass_args=True, pass_kwargs=True)

    def update_bounds(self) -> None:
        """Recompute the span cell bounds from its anchor cells."""
        x0 = self._cell_x0y0.get_x()
        x1 = self._cell_x1y1.get_x() + self._cell_x1y1.get_width()
        y0 = self._cell_x0y0.get_y()
        y1 = self._cell_x1y1.get_y() + self._cell_x1y1.get_height()
        if None not in (x0, y0, x1, y1):
            self.set_bounds(x0, y0, x1 - x0, y1 - y0)


def _expand_indexlike_types(items) -> list:
    if isinstance(items, _IndexLikeType):
        items = items.to_list()
    items = _ensure_list(items)

    expanded_items = []
    for item in items:
        if isinstance(item, _IndexLikeType):
            expanded_items.extend(item.to_list())
        else:
            expanded_items.append(item)
    return expanded_items


def _int_or_indexpos(item: Any, index: pd.Index | pd.MultiIndex, enforce_unique=False) -> list[int]:
    # unwrap Index-like containers
    if hasattr(item, "to_list"):
        item_list = item.to_list()
        if len(item_list) != 1:
            raise ValueError(f"Only index of length 1 supported, got {item}")
        item = item_list[0]

    if isinstance(item, int):
        return [item]

    else:  # do not check item type to allow for all possible index-types
        if item not in index:
            raise KeyError(f"Item '{item}' not in index {index}")

        loc = index.get_loc(item)

        # unique index
        if isinstance(loc, int):
            return [loc]

        if enforce_unique:
            raise ValueError(f"Index position for '{item}' not unique. Try integer indexing.")

        # duplicate contiguous entries
        if isinstance(loc, slice):
            return list(range(loc.start, loc.stop))

        # duplicate non-contiguous entries
        if isinstance(loc, (np.ndarray, list)):
            return np.flatnonzero(loc).tolist()

        raise TypeError(f"Unsupported get_loc result type: {type(loc)}")


def _list_index_strict(lst, value):
    """Find the index of an element in a list.

    Compared to `lst.index(value)` this function does not only compare by `==` but also
    the type. This is relevant to get the first position of 0 in a list with False values.
    """
    return next(i for i, v in enumerate(lst) if v == value and type(v) is type(value))


def _ensure_list(item) -> list:
    if not isinstance(item, list):
        return [item]
    else:
        return item


def add_table_multispan_cell(
    table: Table,
    y0x0: tuple[int],
    width: int,
    height: int,
    facecolor: str = "lightgrey",
    zorder: int | float = -1,
    linewidth: float = 0,
    **kwargs,
) -> SpanCell:
    """
    Create and add a `SpanCell` spanning a rectangular region of a table.

    The spanning region is defined by its bottom-left table index `x0y0`
    and the number of cells to span horizontally (`width`) and
    vertically (`height`).

    Matplotlib tables follow an Excel-like indexing convention:
    smaller row indices are positioned higher in the table. Since the
    span is computed using decreasing row indices, it extends upwards
    from `x0y0` and rightwards across columns.

    Parameters
    ----------
    table : Table
        The table containing the cells to be spanned.
    y0x0 : tuple[int, int]
        Tuple of (row, column) specifying the bottom-left anchor cell.
    width : int
        Number of columns to span to the right.
    height : int
        Number of rows to span upwards.
    facecolor : str or tuple, optional, default "lightgrey"
        Background color of the spanning cell.
    zorder : float, optional, default -1
        Drawing order of the span cell. Lower values draw behind
        regular cells, higher values draw in front.
    linewidth : float, optional, default 0
        Border line width of the span cell.
    **kwargs
        Additional keyword arguments. Arguments applicable to
        `Cell` are passed to the `SpanCell` constructor. Remaining
        arguments are applied via `SpanCell.set()`.

    Returns
    -------
    SpanCell
        The created spanning cell instance.


    Notes
    -----
    The function assumes that all cells within the specified region
    already exist in the table.
    """
    (y0, x0) = y0x0
    (y1, x1) = (y0 - height + 1, x0 + width - 1)
    x0y0_cell = table.get_celld()[(y0, x0)]
    x1y1_cell = table.get_celld()[(y1, x1)]

    cell_kwargs, set_kwargs = separate_kwargs([Cell], **kwargs)
    span_cell = SpanCell(table, x0y0_cell, x1y1_cell, facecolor=facecolor, **cell_kwargs)
    span_cell.set(zorder=zorder, linewidth=linewidth, **set_kwargs)
    return span_cell


def _get_approx_ideal_figsize(ax: Axes, table: Table) -> tuple[float, float]:
    """Get approximation or required figheight to fit all table.

    Logic in a nutshell:
        ideal_figheight =  headerspace + footerspace + tableheight
        ideal_figwidth = ncol * max_coltext_width + max_collabel_width
    """
    fig = ax.get_figure()

    # figheight
    fig_height = fig.get_figheight()
    ax_height_inch = ax.get_position().height * fig_height
    header_footer_space = fig_height - ax_height_inch
    table_height = table.get_window_extent().height / fig.dpi
    # scale if we are in a scaled figsize_context.
    ideal_figheight = table_height + header_footer_space

    # width
    ncols = max(col for (_, col) in table.get_celld().keys() if col >= 0) + 1
    max_width_cells = 0
    max_width_cell_labels = 0
    for (row, col), cell in table.get_celld().items():
        text_width = get_text_bbox(cell.get_text()).width_inch

        if col == -1:
            max_width_cell_labels = max(max_width_cell_labels, text_width)
        else:
            max_width_cells = max(max_width_cells, text_width)

    ideal_figwidth = ncols * max_width_cells + max_width_cell_labels
    # in general we seem to underestimate the necessary width, therefore we add a bit
    ideal_figwidth += 1.2  # in inch
    return ideal_figheight, ideal_figwidth


def _construct_property_applier(
    text_props=None,
    pad=None,
    height_scaling=None,
    visible_edges=None,
    custom_modifiers: list[Callable[[Cell], Any]] | None = None,
    **kwargs,
) -> Callable[[Cell], None]:
    text_props = text_props or {}

    def property_applier(cell: Cell) -> None:
        cell.set(**kwargs)
        cell.set_text_props(**text_props)
        if pad is not None:
            cell.PAD = pad
        if visible_edges is not None:
            cell.visible_edges = visible_edges
        if custom_modifiers is not None:
            for modifier in _ensure_list(custom_modifiers):
                assert isinstance(modifier, Callable), f"passed custom modifier must be a callable. Got {modifier}"
                modifier(cell)
        if height_scaling is not None:
            cell.set_height(cell.get_height() * height_scaling)

    return property_applier


def _merge_with_defaults(defaults: dict, user: dict | None) -> dict:
    """Merge user-provided properties into defaults."""
    defaults = defaults.copy()
    if user is None:
        return defaults

    user = user.copy()

    # merge text props on item level

    text_props = {**defaults.pop("text_props", {}), **user.pop("text_props", {})}
    return {**defaults, **user, "text_props": text_props}


def apply_table_cell_property(
    table: Table,
    row: int,
    col: int,
    property_dict: dict,
) -> None:
    """
    Apply a property dictionary to a single table cell.

    Parameters
    ----------
    table : matplotlib.table.Table
    row : int
        Absolute row index.
    col : int
        Absolute column index.
    property_dict : dict
        Property dictionary as described in the `Property Dictionaries` section of
        [make_table]

    """
    cell = table.get_celld()[(row, col)]
    _construct_property_applier(**property_dict)(cell)


def apply_table_row_property(
    table: Table,
    row: int,
    property_dict: dict,
) -> None:
    """
    Apply a property dictionary to all cells in a given table row.

    Parameters
    ----------
    table : matplotlib.table.Table
    row : int
        Absolute row index in the rendered table.
    property_dict : dict
        Property dictionary as described in the `Property Dictionaries` section of
        [make_table]


    See Also
    --------
    - [make_table](#make_table)
    - [apply_table_cell_property](#apply_table_cell_property)
    - [apply_table_col_property](#apply_table_col_property)
    - [apply_table_range_property](#apply_table_range_property)
    """
    for r, c in table.get_celld().keys():
        if r == row:
            apply_table_cell_property(table, r, c, property_dict)


def apply_table_col_property(
    table: Table,
    col: int,
    property_dict: dict,
) -> None:
    """
    Apply a property dictionary to all cells in a given table column.

    Parameters
    ----------
    table : matplotlib.table.Table
    col : int
        Absolute column index in the rendered table.
        Use -1 for the row-label column.
    property_dict : dict
        Property dictionary as described in the `Property Dictionaries` section of
        [make_table](#make_table).

    See Also
    --------
    - [make_table](#make_table)
    - [apply_table_cell_property](#apply_table_cell_property)
    - [apply_table_row_property](#apply_table_row_property)
    - [apply_table_range_property](#apply_table_range_property)
    """
    for r, c in table.get_celld().keys():
        if c == col:
            apply_table_cell_property(table, r, c, property_dict)


def apply_table_range_property(
    table: Table,
    bottom_left: tuple[int, int],
    top_right: tuple[int, int],
    property_dict: dict,
) -> None:
    """
    Apply a property dictionary to a rectangular cell range (inclusive).

    Parameters
    ----------
    table : matplotlib.table.Table

    bottom_left : tuple[int, int]
        (row, col) of the bottom-left cell.

    top_right : tuple[int, int]
        (row, col) of the top-right cell.

    property_dict : dict
        Property dictionary as described in the `Property Dictionaries` section of
        [make_table](#make_table).

    See Also
    --------
    - [make_table](#make_table)
    - [apply_table_cell_property](#apply_table_cell_property)
    - [apply_table_row_property](#apply_table_row_property)
    - [apply_table_col_property](#apply_table_col_property)
    """
    r_bottom, c_left = bottom_left
    r_top, c_right = top_right

    # matplotlib tables use smaller row indices higher in the table
    r_min, r_max = min(r_top, r_bottom), max(r_top, r_bottom)
    c_min, c_max = min(c_left, c_right), max(c_left, c_right)

    for r, c in table.get_celld().keys():
        if r_min <= r <= r_max and c_min <= c <= c_max:
            apply_table_cell_property(table, r, c, property_dict)

def make_table(
    df,
    ax: Axes | None = None,
    title_rows: Sequence[tuple[row, str] | tuple[row, str, PropertyDict]] | None = None,
    empty_rows: Sequence[row] | None = None,
    empty_cols: Sequence[col] | None = None,
    bold_header_levels: Sequence[int] | None = None,
    header_spanning: bool = True,
    break_header_span: col | Sequence[col] | None = None,
    span_cells: Sequence[tuple[row_col, width, height] | tuple[row_col, width, height, PropertyDict]] | None = None,
    table_properties: TablePropertyDict | None = None,
    row_properties: Sequence[tuple[row | Sequence[row], PropertyDict]] | None = None,
    col_properties: Sequence[tuple[col | Sequence[col], PropertyDict]] | None = None,
    cell_properties: Sequence[tuple[row_col | Sequence[row_col], PropertyDict]] | None = None,
    all_cell_properties: PropertyDict | None = None,
    body_cell_properties: PropertyDict | None = None,
    header_cell_properties: PropertyDict | None = None,
    title_row_properties: PropertyDict | None = None,
    row_label_properties: PropertyDict | None = None,
    autodetect_latex: bool = True,
    extraspace_header: float = 0,
    extraspace_footer: float = 0,
) -> Table:
    """
    Create a formatted Matplotlib table from a pandas DataFrame.

    This function renders a `pandas.DataFrame` as a `matplotlib.table.Table`
    with consistent styling and flexible structural customisation.

    Supported features include:

    - MultiIndex column headers with optional automatic horizontal cell
      spanning (i.e. visual merging of adjacent header cells)
    - Explicit header span breaks
    - Optional title rows
    - Inserted empty rows and columns
    - Arbitrary row, column, and cell styling
    - Explicit span cells
    - Table-, header-, body-, and label-specific styling
    - Automatic figure sizing if no `ax` is provided
    - Automatic LaTeX detection and rendering
    - Header and footer spacing adjustments

    Row and column references may be provided either as:

    - integers: refer to positional indices relative to the original DataFrame
        - When used as a column reference, -1 refers to the index column.
        - When used as a row reference, negative integers refer to header rows, where
          -1 denotes the header row closest to the table body.
    - strings: label-based references from the original DataFrame index or columns

    The table follows Matplotlib’s indexing convention:
    smaller row indices are positioned higher in the rendered table.

    Parameters
    ----------
    df : pandas.DataFrame
        The data to render. Supports single-level and MultiIndex columns.

    ax : matplotlib.axes.Axes | None, optional
        Target axes. If None, a new figure and axes are created
        with automatic figsize.

    title_rows : Sequence[tuple[row, str] | tuple[row, str, PropertyDict]] | None, optional
        Insert full-width title rows before the specified data row.

        Each entry must be:

            (row, title_text)
            (row, title_text, property_dict)

        The optional `property_dict` follows the same structure
        as described in the Property Dictionaries section below.

        Example:

        ```python
        title_rows=[(0, "Section A")]
        title_rows=[("Total", "Summary", {"edgecolor": "lightgrey"})]
        ```

    empty_rows : Sequence[row] | None, optional
        Insert empty spacer rows before the specified data rows.

        Example:

        ```python
        # Inserts an empty row above data row at position 2
        empty_rows=[2]
        # Inserts an empty row above the row with index label "Total"
        empty_rows=["Total"]
        ```

    empty_cols : Sequence[col] | None, optional
        Insert empty spacer columns before the specified data columns.
        `empty_cols` can be used as a layout adjustment mechanism.
        In particular, inserting an empty column at position `0` is a simple
        way to increase the visual width of the row-label column.

        Example:

        ```python
        empty_cols=[1]
        empty_cols=["B"]
        # Increase row-label column width
        empty_cols=[0]
        ```

    bold_header_levels : Sequence[int] | None, optional
        Header row indices within the header block that should be bold.
        These indices refer to header levels, not DataFrame rows.

        Example:

        ```python
            bold_header_levels=[0]
        ```


    header_spanning : bool, default True
        Enable or disable automatic header span simulation for MultiIndex columns.
        See also the `Header Spanning` section below.

    break_header_span : col | Sequence[col] | None, optional
        MultiIndex column keys where header spanning should be explicitly broken.
        The span is broken *to the left* of the specified column.

        Example:

        ```python
        df = pd.DataFrame({("A", "L1"): [1], ("A", "L2"): [1], ("B", "L3"): [1]})

        # By default, plotting this df would Span ("A", "L1") and ("A", "L2")
        # because the top level header "A" is the same.
        # To break the span between ("A", "L1") and ("A", "L2"), provide ("A", "L2"):

        plt.make_table(df, break_header_span=[("A", "L2")])
        ```

    span_cells : Sequence[tuple[row_col, width, height] | tuple[row_col, width, height, PropertyDict]] | None, optional
        Additional span cells.

        Each entry must be:

            ((row, col), width, height)
            ((row, col), width, height, property_dict)

        Here:

        - `row` refers to a data row of the original DataFrame
        - `col` refers to a data column of the original DataFrame

        The optional `property_dict` follows the structure
        described in the Property Dictionaries section.


        Example:

        ```python
        span_cells=[((4, 0), 2, 2, {"facecolor": "lightgrey"})]
        ```


    table_properties : TablePropertyDict | None, optional
        Properties forwarded to `Axes.table()`.

    row_properties : Sequence[tuple[row | Sequence[row], PropertyDict]] | None, optional
        Row-level styling.

        Each entry must be:

            (row, property_dict)

        The provided `property_dict` is applied to all cells
        belonging to the specified data row.

        Example:

        ```python
        row_properties=[(0, {"facecolor": "lightgrey"})]
        ```

    col_properties : Sequence[tuple[col | Sequence[col], PropertyDict]] | None, optional
        Column-level styling.

        Each entry must be:

            (col, property_dict)

        The provided `property_dict` is applied to all cells
        belonging to the specified data column.

        Example:

        ```python
        col_properties=[("Revenue", {"text_props": {"weight": "bold"}})]
        ```


    cell_properties : Sequence[tuple[row_col | Sequence[row_col], PropertyDict]] | None, optional
        Cell-level styling.

        Each entry must be:

            ((row, col), property_dict)

        The provided `property_dict` is applied to the specific cell
        identified by `(row, col)`.

        Here:

        - `row` refers to a data row in the original DataFrame
        - `col` refers to a data column in the original DataFrame


        Example:

        ```python
        cell_properties=[((0, "Revenue"), {"facecolor": "lightgrey"})]
        ```

    all_cell_properties : PropertyDict | None, optional
        The provided `PropertyDict` is applied to all cells in the table, including
        header and row-label cells.

    body_cell_properties : PropertyDict | None, optional
        The provided `PropertyDict` is applied to all cells in the table body, i.e.
        excluding header and row-labels.

    header_cell_properties : PropertyDict | None, optional
        The provided `PropertyDict` is applied to all header cells.

    title_row_properties : PropertyDict | None, optional
        The provided `PropertyDict` is used as default properties for all
        generated title rows.

    row_label_properties : PropertyDict | None, optional
        The provided `PropertyDict` is applied to all cells in the row-label
        column in body rows.

    autodetect_latex : bool, default True
        Per cell, automatically set `usetex=True` if LaTeX text is detected.

    extraspace_header : float, optional
        Additional vertical space above the table (in inches).

    extraspace_footer : float, optional
        Additional vertical space below the table (in inches).

    Returns
    -------
    matplotlib.table.Table
        The created Matplotlib table instance.

    Property Dictionaries
    ---------------------

    The following parameters accept a `property_dict`:

    - row_properties
    - col_properties
    - cell_properties
    - all_cell_properties
    - body_cell_properties
    - header_cell_properties
    - title_row_properties
    - row_label_properties
    - span_cells (optional fourth element)
    - title_rows (optional third element)

    Each property dictionary may contain the following keys:

    | Property | Description |
    |-----------|------------|
    | `text_props` | Forwards text styling to `cell.set_text_props(**text_props)`.<br>Example: `{"text_props": {"weight": "bold", "ha": "right"}}` |
    | `pad` | Sets internal cell padding via `cell.PAD = pad`.<br>Example: `{"pad": 0.2}` |
    | `height_scaling` | Multiplies the current cell height using `cell.set_height(cell.get_height() * x)`.<br>Example: `{"height_scaling": 1.4}` |
    | `visible_edges` | Controls which cell borders are visible via `cell.visible_edges`.<br>Example: `{"visible_edges": "L"}` |
    | `custom_modifiers` | Executes one or more callables on the cell after other properties are applied.<br>Example: `{"custom_modifiers": [lambda c: c.set_edgecolor("red")]}` |
    | Any other keyword | Forwarded directly to `cell.set(**kwargs)` and therefore supports all native `matplotlib.table.Cell` properties. For the complete list of supported properties, refer to https://matplotlib.org/stable/api/table_api.html#matplotlib.table.Cell.set. <br>Example: `{"facecolor": "lightgrey", "linewidth": 0.8}` |

    Header Spanning Behaviour
    -------------------------
    - Spanning is applied independently on each header level except
      the lowest level.
    - On a given level, adjacent labels are blanked if:
        1. They are equal, and
        2. No parent level changed between the two columns. I.e. Parent-level changes
        automatically prevent spanning on deeper levels. This ensures that spanning
        respects hierarchical boundaries.
    - The lowest header level never spans;
    - `break_header_span` specifies column keys where a span should be
      explicitly broken. **Important**: The span is broken *to the left* of the specified column.

    Notes
    -----
    - Integers refer to positional indices relative to the original DataFrame.
        - When used as a column reference, -1 refers to the index column.
        - When used as a row reference, negative integers refer to header rows,
          where -1 denotes the header row closest to the table body.
    - Strings refer to label-based references from the original DataFrame index or columns.
    - Passed property dictionaries override sensible defaults.
    - Most parameters that accept row, column, cell, or span selectors support
      multiple elements. A selector may be provided either as a single element
      or as a sequence of elements. When a sequence is provided, the specified
      operation or styling is applied to all referenced rows, columns, or cells._property)
    """
    assert not isinstance(df.index, pd.MultiIndex), "Currently no support for MultiIndex in the Rows"
    # Catch all function input in raw version. This MUST be at the beginning of the funciton.
    raw_fuction_inputs = locals().copy()

    # If no ax is passed, we create a figure in a reasonable size
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 15))
        table = make_table(**{**raw_fuction_inputs, **{"ax": ax}})
        ideal_figheight, ideal_figwidth = _get_approx_ideal_figsize(ax, table)
        plt.close(fig)

        # Create new fig, ax using the approximated ideal figsize
        fig, ax = plt.subplots(figsize=(ideal_figwidth, ideal_figheight))
        plt.sca(ax)
    else:
        fig = ax.get_figure()
    # Process Inputs
    ## Normalise optional list arguments to avoid mutable default issues
    title_rows = [] if title_rows is None else title_rows
    empty_rows = [] if empty_rows is None else empty_rows
    empty_cols = [] if empty_cols is None else empty_cols
    bold_header_levels = [] if bold_header_levels is None else bold_header_levels
    break_header_span = [] if break_header_span is None else break_header_span
    row_properties = [] if row_properties is None else row_properties
    col_properties = [] if col_properties is None else col_properties
    cell_properties = [] if cell_properties is None else cell_properties
    span_cells = [] if span_cells is None else span_cells

    ## Default Properties
    default_table_properties = dict(
        cellLoc="right",
        loc="upper left",
        edges="B",
    )
    default_cell_properties = dict(
    )
    default_body_cell_properties = dict()
    default_header_properties = dict(
        text_props=dict(ha="left", va="bottom"),
        height_scaling=1.4,
        pad=0.1,
    )
    default_title_row_properties = dict(
        zorder=0,
        facecolor="white",
        text_props=dict(weight="bold", ha="left", va="top"),
        height_scaling=1.4,
        pad=0,
    )
    default_row_label_properties = dict(
        text_props=dict(ha="left"),
        pad=0,
    )

    table_properties = _merge_with_defaults(default_table_properties, table_properties)
    all_cell_properties = _merge_with_defaults(default_cell_properties, all_cell_properties)
    body_cell_properties = _merge_with_defaults(default_body_cell_properties, body_cell_properties)
    header_cell_properties = _merge_with_defaults(default_header_properties, header_cell_properties)
    title_row_properties = _merge_with_defaults(default_title_row_properties, title_row_properties)
    row_label_properties = _merge_with_defaults(default_row_label_properties, row_label_properties)

    # compared to charts we want less space below the header, thus we
    # remove the default-space, which turned out to give good results
    default_space_header_to_table = 0
    extraspace_header = -default_space_header_to_table + extraspace_header

    # we later need the original dataframe and also dont want to modify the passed one
    df_orig = df.copy()
    df = df.copy()

    # list that initially stores all column pos as int. Later we insert elements into
    # this list, which moves these integers and allows to compare value vs list.index(value)
    # to find the position of a column in the original dataframe in the new dataframe
    original_column_mapping = list(range(len(df.columns)))

    def get_rowindex(items, original_index_mapping) -> list:
        items = _expand_indexlike_types(items)

        # map item to its row index in the original dataframe
        items_orig_indexpos = []
        for item in items:
            indexpos = _int_or_indexpos(item, df_orig.index)
            items_orig_indexpos.extend(indexpos)

        # map the column index of the original dataframe to the new one
        items_indexpos = []
        for item in items_orig_indexpos:
            # negative values refer to the header rows and are not part of the dataframe
            if item < 0:
                assert -item <= n_header_levels, (
                    f"You tried to use index {item}, however, there are only {n_header_levels} header levels. "
                )
                item_idx = n_header_levels + item

            else:
                item_idx = _list_index_strict(original_index_mapping, item)
            items_indexpos.append(item_idx)
        return items_indexpos

    def get_colindex(items, original_column_mapping) -> list:
        items = _expand_indexlike_types(items)

        # map item to its column index in the original dataframe
        items_orig_indexpos = []
        for item in items:
            indexpos = _int_or_indexpos(item, df_orig.columns)
            items_orig_indexpos.extend(indexpos)

        # map the column index of the original dataframe to the new one
        items_indexpos = []
        for item in items_orig_indexpos:
            # -1 refers to the label column and is not part of the dataframe
            if item in [-1]:
                item_idx = item
            else:
                item_idx = _list_index_strict(original_column_mapping, item)
            items_indexpos.append(item_idx)
        return items_indexpos

    # Insert empty cols
    j = 0
    for i, col in enumerate(sorted(get_colindex(_ensure_list(empty_cols), original_column_mapping))):
        insert_at = col + j
        df.insert(loc=insert_at, column=f"_emptycol_{i}", value=None)
        original_column_mapping.insert(insert_at, False)
        j = i + 1

    # Build header rows (MultiIndex aware)
    ## allow integer indexing
    _break_header_span = []
    for breakpoint in _ensure_list(break_header_span):
        if isinstance(breakpoint, int):
            assert breakpoint >= 0, f"Cannot break span at negative position {breakpoint}"
            _break_header_span.append(df_orig.columns[breakpoint])
        else:
            _break_header_span.append(breakpoint)
    break_header_span = _break_header_span
    header_rows, n_header_levels = _build_header_rows(df, header_spanning, break_header_span)

    # Insert Additional Elements
    # Normalize title_rows
    title_rows = _ensure_list(title_rows)
    title_rows.sort(key=lambda x: _int_or_indexpos(x[0], df_orig.index, enforce_unique=True)[0])
    # --------------------
    # Format body
    # --------------------
    ## start with header
    cell_text = header_rows
    row_labels = [""] * n_header_levels
    original_index_mapping = [False] * n_header_levels
    title_lookup = {}

    def format_value_as_celltext(value):
        if pd.isna(value):
            return ""
        else:
            return str(value)

    ## add data as is below header
    for i, (idx, row) in enumerate(df.iterrows()):
        cell_text.append([format_value_as_celltext(value) for value in row])
        row_labels.append(idx)
        original_index_mapping.append(i)

    ## insert empty_rows
    for empty_row in _ensure_list(empty_rows):
        insert_at = get_rowindex(empty_row, original_index_mapping)[0]
        cell_text.insert(insert_at, [""] * len(df.columns))
        row_labels.insert(insert_at, "")
        original_index_mapping.insert(insert_at, False)

    ## insert title_rows
    for title_row, title_text, *title_properties in title_rows:
        title_properties = title_properties[0] if title_properties else {}
        insert_at = get_rowindex(title_row, original_index_mapping)[0]
        title_lookup[insert_at] = (title_text, title_properties)
        cell_text.insert(insert_at, [""] * len(df.columns))
        row_labels.insert(insert_at, "")
        original_index_mapping.insert(insert_at, False)
    # --------------------
    # Render table
    # --------------------
    ax.axis("off")

    table = ax.table(
        cellText=cell_text,
        rowLabels=row_labels,
        **table_properties,
    )

    table.auto_set_font_size(False)
    table.scale(1, 1.4)
    table.AXESPAD = 0

    if hasattr(fig, "add_extraspace_header"):
        fig.add_extraspace_header(extraspace_header)
    if hasattr(fig, "add_extraspace_footer"):
        fig.add_extraspace_footer(extraspace_footer)

    # styling
    property_applier = _construct_property_applier(**all_cell_properties)
    for (row, col), cell in table.get_celld().items():
        property_applier(cell)

    property_applier = _construct_property_applier(**body_cell_properties)
    for (row, col), cell in table.get_celld().items():
        # only apply to body cells
        if (row < n_header_levels) or (col == -1):
            continue
        property_applier(cell)

    if autodetect_latex:
        for (row, col), cell in table.get_celld().items():
            text = cell.get_text().get_text()
            if requires_usetex(text):
                cell.get_text().set_usetex(True)
    ## header rows
    property_applier = _construct_property_applier(**header_cell_properties)
    for (row, col), cell in table.get_celld().items():
        # only apply to header rows
        if row >= n_header_levels:
            continue

        property_applier(cell)

        if row in _ensure_list(bold_header_levels):
            cell.set_text_props(weight="bold")

        # no vertical line for row-label column and for merged header cells (sets text = "")
        if col == -1 or cell.get_text().get_text() == "":
            cell.visible_edges = ""
        else:
            cell.visible_edges = "L"

    ## title rows

    for title_row, (title_text, title_properties) in title_lookup.items():
        multispan_cell_kwargs = _merge_with_defaults(title_row_properties, title_properties)

        text_props = multispan_cell_kwargs.pop("text_props")
        pad = multispan_cell_kwargs.pop("pad")
        height_scaling = multispan_cell_kwargs.pop("height_scaling")
        custom_modifiers = multispan_cell_kwargs.pop("custom_modifiers", [])
        if autodetect_latex:
            if text_props.get("usetex", None) is None:
                if requires_usetex(title_text):
                    text_props["usetex"] = True
        x0, y0 = (-1, title_row)
        height = 1
        width = len(df.columns) + 1  # data-cols + row-labels

        span_cell = add_table_multispan_cell(table, (y0, x0), width, height, text=title_text, **multispan_cell_kwargs)
        span_cell.set_text_props(**text_props)
        span_cell.PAD = pad
        for modifier in custom_modifiers:
            modifier(span_cell)

        for (row, col), cell in table.get_celld().items():
            if row == title_row:
                cell.set_height(cell.get_height() * height_scaling)

    ## label col
    property_applier = _construct_property_applier(**row_label_properties)
    for (row, col), cell in table.get_celld().items():
        # only apply to row-label cells in body-rows
        if col == -1 and row >= n_header_levels:
            property_applier(cell)

    # Span Cells
    for (y0, x0), width, height, *rest in span_cells:
        kwargs = rest[0] if rest else {}
        y0 = get_rowindex(y0, original_index_mapping)[0]
        x0 = get_colindex(x0, original_column_mapping)[0]
        add_table_multispan_cell(table, (y0, x0), width, height, **kwargs)

    for rows, property_dict in row_properties:
        resolved_rows = get_rowindex(rows, original_index_mapping)
        for r in resolved_rows:
            apply_table_row_property(table, r, property_dict)

    for cols, property_dict in col_properties:
        resolved_cols = get_colindex(cols, original_column_mapping)
        for c in resolved_cols:
            apply_table_col_property(table, c, property_dict)

    for cells, property_dict in cell_properties:
        for row, col in _ensure_list(cells):
            r = get_rowindex(row, original_index_mapping)[0]
            c = get_colindex(col, original_column_mapping)[0]
            apply_table_cell_property(table, r, c, property_dict)

    return table


def _build_header_rows(df: pd.DataFrame, header_spanning: bool, break_header_span):
    """
    Build header rows for `make_table`.

    Supports single-level and MultiIndex columns. For MultiIndex columns,
    repeated labels can be blanked to simulate horizontal spanning, while
    respecting explicit span breaks and artificial "_emptycol" columns.

    - Empty strings are replaced with a single space to enforce correct rendering.
    - Columns whose top-level label starts with "_emptycol" are treated
      as layout helper columns. These columns:
        - Are rendered with empty labels on all header levels.
        - Do not participate in span detection.
        - Do not influence parent-level comparisons.

    Parameters
    ----------
    df : pandas.DataFrame
    header_spanning : bool
    break_header_span : tuple | _IndexLikeType | list[tuple | _IndexLikeType] | None
        Iterable of full column keys (MultiIndex tuples) where a
        horizontal span should be broken.

    Returns
    -------
    header_rows : list[list[str]]
        Header texts per level (top to bottom).
    n_header_levels : int
        Number of header levels.
    """
    header_rows = []

    if isinstance(df.columns, pd.MultiIndex):
        n_header_levels = df.columns.nlevels
        col_tuples = list(df.columns)

        # cache all level values once to avoid repeated lookups
        level_values = [df.columns.get_level_values(level).tolist() for level in range(n_header_levels)]

        # Identify which columns are artificial empty columns
        emptycol_mask = [isinstance(col[0], str) and col[0].startswith("_emptycol") for col in col_tuples]

        for level in range(n_header_levels):
            values = level_values[level].copy()

            # ensure empty helper columns remain empty on all levels
            for j, is_emptycol in enumerate(emptycol_mask):
                if is_emptycol:
                    values[j] = ""

            # simulate horizontal spanning for all but the lowest level
            if level < n_header_levels - 1 and header_spanning:
                last_value = object()

                for j, current_value in enumerate(values):
                    full_key = col_tuples[j]

                    # Break span explicitly if requested
                    if full_key in _expand_indexlike_types(break_header_span):
                        last_value = object()

                    # Skip added empty columns
                    if emptycol_mask[j]:
                        continue

                    # Detect whether any parent level changed
                    parent_break = False
                    if level > 0 and j > 0:
                        for parent_level in range(level):
                            if level_values[parent_level][j] != level_values[parent_level][j - 1]:
                                parent_break = True
                                break

                    # Span only if same value AND no parent break
                    if j > 0 and current_value == last_value and not parent_break:
                        values[j] = ""
                        continue

                    # Rendering workaround for empty strings
                    if isinstance(current_value, str) and current_value == "":
                        values[j] = " "

                    last_value = current_value

            # Force break rendering on lowest header level
            if level == n_header_levels - 1:
                for j, v in enumerate(values):
                    if emptycol_mask[j]:
                        continue
                    if v == "":
                        values[j] = " "

            header_rows.append(values)

    else:
        # single-level columns
        columns = []
        for value in df.columns.tolist():
            if isinstance(value, str) and value.startswith("_emptycol"):
                columns.append("")
            else:
                columns.append(value)

        header_rows.append(columns)
        n_header_levels = 1

    return header_rows, n_header_levels


