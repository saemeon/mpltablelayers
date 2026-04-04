"""Helpers to plot nice tables.

See Also
--------
- [Matplotlib Table API](https://matplotlib.org/stable/api/table_api.html#matplotlib.table.table)
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

import numpy as np
import pandas as pd
from matplotlib.table import Cell, Table

from .utils import separate_kwargs

__all__ = [
    "HeaderSpan",
    "SpanCell",
    "add_hierarchical_header",
    "add_table_multispan_cell",
    "apply_table_cell_property",
    "apply_table_col_property",
    "apply_table_property",
    "apply_table_range_property",
    "apply_table_row_property",
    "resolve_header_spans",
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


@dataclass
class HeaderSpan:
    """A resolved span group within a hierarchical header.

    Represents a contiguous range of columns at a specific header level
    that share the same label and should be visually merged.

    Attributes
    ----------
    level : int
        Header level index (0 = topmost).
    label : str
        The header label text.
    start_col : int
        First column index (inclusive).
    end_col : int
        Last column index (inclusive).
    """

    level: int
    label: str
    start_col: int
    end_col: int

    @property
    def width(self) -> int:
        """Number of columns this span covers."""
        return self.end_col - self.start_col + 1


class SpanCell(Cell):
    """A table cell that spans a rectangular region defined by two anchor cells.

    `SpanCell` derives its position and size from two existing table cells.
    In matplotlib's table indexing (row 0 at the top, increasing downward):

    - `cell_x0y0` defines the bottom-left corner of the spanned region
      (highest row index, lowest column index).
    - `cell_x1y1` defines the upper-right corner of the spanned region
      (lowest row index, highest column index).

    The span cell dynamically tracks changes of the anchor cells. Whenever
    either anchor cell changes its position or size, the span cell updates
    its own bounds accordingly.

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

        # Wrap anchor-cell methods so that this span cell stays in sync
        self._hook(cell_x0y0, "set_x", self.update_bounds)
        self._hook(cell_x0y0, "set_y", self.update_bounds)
        self._hook(cell_x1y1, "set_x", self.update_bounds)
        self._hook(cell_x1y1, "set_width", self.update_bounds)
        self._hook(cell_x1y1, "set_y", self.update_bounds)
        self._hook(cell_x1y1, "set_height", self.update_bounds)
        self._hook(cell_x0y0, "set_figure", self.set_figure, forward_args=True)
        self._hook(cell_x0y0, "set_transform", self.set_transform, forward_args=True)

    @staticmethod
    def _hook(obj, method_name: str, callback: Callable, *, forward_args: bool = False) -> None:
        """Wrap a method on *obj* so that *callback* fires after each call."""
        original = getattr(obj, method_name)

        @functools.wraps(original)
        def wrapper(*args, **kwargs):
            result = original(*args, **kwargs)
            if forward_args:
                callback(*args, **kwargs)
            else:
                callback()
            return result

        setattr(obj, method_name, wrapper)

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


def apply_table_property(
    table: Table,
    property_dict: dict,
) -> None:
    """
    Apply a property dictionary to every cell in the table.

    Parameters
    ----------
    table : matplotlib.table.Table
    property_dict : dict
        See `apply_table_cell_property` for supported keys.
    """
    property_applier = _construct_property_applier(**property_dict)
    for cell in table.get_celld().values():
        property_applier(cell)


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
        Property dictionary supporting the following keys:

        | Key | Effect |
        |-----|--------|
        | ``text_props`` | Forwarded to ``cell.set_text_props(**text_props)`` |
        | ``pad`` | Sets ``cell.PAD`` |
        | ``height_scaling`` | Multiplies current cell height |
        | ``visible_edges`` | Sets ``cell.visible_edges`` |
        | ``custom_modifiers`` | List of callables invoked with the cell |
        | Any other key | Forwarded to ``cell.set(**kwargs)`` |
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
        See `apply_table_cell_property` for supported keys.

    See Also
    --------
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
        See `apply_table_cell_property` for supported keys.

    See Also
    --------
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
        See `apply_table_cell_property` for supported keys.

    See Also
    --------
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


def resolve_header_spans(
    columns: pd.Index | pd.MultiIndex,
    *,
    spanning: bool = True,
    break_span: col | Sequence[col] | None = None,
    empty_col_prefix: str = "_emptycol",
) -> tuple[list[HeaderSpan], int]:
    """Analyze a column index and resolve header span groups.

    For a ``MultiIndex``, identifies groups of adjacent columns that share
    the same label at each level and should be visually merged.  Respects
    hierarchical boundaries: a parent-level label change always breaks
    child-level spans.

    Parameters
    ----------
    columns : pd.Index | pd.MultiIndex
        The column index to analyze.
    spanning : bool, default True
        Whether to merge adjacent identical labels into spans.
        When False, every column produces its own single-width span.
    break_span : col | Sequence[col] | None, optional
        Column keys where spanning should be explicitly broken.
        The break occurs *to the left* of the specified column.
    empty_col_prefix : str, default "_emptycol"
        Column label prefix identifying layout-only spacer columns.
        Columns matching this prefix are excluded from spans but do not
        break them; a span may visually cover the gap.

    Returns
    -------
    spans : list[HeaderSpan]
        Resolved span groups, ordered by level then by column position.
    n_levels : int
        Number of header levels.

    Examples
    --------
    >>> idx = pd.MultiIndex.from_tuples([
    ...     ("A", "x"), ("A", "y"), ("B", "x"), ("B", "y"),
    ... ])
    >>> spans, n = resolve_header_spans(idx)
    >>> [(s.label, s.start_col, s.width) for s in spans if s.width > 1]
    [('A', 0, 2), ('B', 2, 2)]
    """
    break_span = _ensure_list(break_span) if break_span is not None else []
    break_keys = set(_expand_indexlike_types(break_span))

    def _is_empty_col(label) -> bool:
        return isinstance(label, str) and label.startswith(empty_col_prefix)

    # Single-level index: one span per column, no merging
    if not isinstance(columns, pd.MultiIndex):
        spans = []
        for j, label in enumerate(columns):
            if _is_empty_col(label):
                continue
            spans.append(HeaderSpan(level=0, label=str(label), start_col=j, end_col=j))
        return spans, 1

    n_levels = columns.nlevels
    col_tuples = list(columns)
    level_values = [columns.get_level_values(lvl).tolist() for lvl in range(n_levels)]
    emptycol_mask = [_is_empty_col(t[0]) for t in col_tuples]

    spans: list[HeaderSpan] = []

    for level in range(n_levels):
        values = level_values[level]
        is_spannable = level < n_levels - 1 and spanning

        current_label = None
        current_start = None
        current_end = None
        prev_non_empty_j = None

        for j in range(len(values)):
            if emptycol_mask[j]:
                continue

            should_start_new = False

            if current_label is None:
                should_start_new = True
            elif not is_spannable:
                should_start_new = True
            elif values[j] != current_label:
                should_start_new = True
            elif col_tuples[j] in break_keys:
                should_start_new = True
            elif level > 0 and prev_non_empty_j is not None:
                for parent in range(level):
                    if level_values[parent][j] != level_values[parent][prev_non_empty_j]:
                        should_start_new = True
                        break

            if should_start_new:
                if current_label is not None:
                    spans.append(HeaderSpan(level, str(current_label), current_start, current_end))
                current_start = j
                current_label = values[j]

            current_end = j
            prev_non_empty_j = j

        if current_label is not None:
            spans.append(HeaderSpan(level, str(current_label), current_start, current_end))

    return spans, n_levels


def add_hierarchical_header(
    table: Table,
    columns: pd.Index | pd.MultiIndex,
    *,
    start_row: int = 0,
    start_col: int = 0,
    spanning: bool = True,
    break_span: col | Sequence[col] | None = None,
    empty_col_prefix: str = "_emptycol",
    default_properties: PropertyDict | None = None,
    level_properties: dict[int, PropertyDict] | None = None,
    label_properties: dict[str, PropertyDict] | None = None,
) -> list[SpanCell]:
    """Construct a hierarchical header on a table using SpanCells.

    Analyzes the column index to find span groups via
    `resolve_header_spans`, then creates a `SpanCell` for each
    multi-column group.  Single-column entries are left as regular
    cells (no SpanCell needed).

    Styling is resolved in priority order (lowest wins):
    ``default_properties`` < ``level_properties`` < ``label_properties``.

    Parameters
    ----------
    table : Table
        The matplotlib table to add header spans to.  The table must
        already contain cells at the positions covered by the header.
    columns : pd.Index | pd.MultiIndex
        Column index defining the header structure.
    start_row : int, default 0
        Table row index where the topmost header level is placed.
    start_col : int, default 0
        Table column index corresponding to the first data column.
    spanning : bool, default True
        Whether to merge adjacent identical labels.
    break_span : col | Sequence[col] | None, optional
        Column keys where spanning should be explicitly broken.
    empty_col_prefix : str, default "_emptycol"
        Prefix for layout-only spacer columns.
    default_properties : PropertyDict | None, optional
        Default styling applied to every created SpanCell.
        Supports the same keys as ``apply_table_cell_property``.
    level_properties : dict[int, PropertyDict] | None, optional
        Per-level styling.  Keys are level indices (0 = topmost).
        Merged on top of *default_properties*.
    label_properties : dict[str, PropertyDict] | None, optional
        Per-label styling.  Keys are label strings.
        Merged on top of level and default properties.

    Returns
    -------
    list[SpanCell]
        The created SpanCell instances, one per multi-column span.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> idx = pd.MultiIndex.from_tuples([
    ...     ("Group A", "x"), ("Group A", "y"),
    ...     ("Group B", "x"), ("Group B", "y"),
    ... ])
    >>> fig, ax = plt.subplots()
    >>> table = ax.table(
    ...     cellText=[[""] * 4] * 3,
    ...     loc="center",
    ... )
    >>> spans = add_hierarchical_header(
    ...     table, idx,
    ...     default_properties={"facecolor": "lightblue"},
    ...     level_properties={0: {"text_props": {"weight": "bold"}}},
    ...     label_properties={"Group A": {"facecolor": "salmon"}},
    ... )
    """
    header_spans, _ = resolve_header_spans(
        columns,
        spanning=spanning,
        break_span=break_span,
        empty_col_prefix=empty_col_prefix,
    )

    default_properties = default_properties or {}
    level_properties = level_properties or {}
    label_properties = label_properties or {}

    span_cells: list[SpanCell] = []

    for span in header_spans:
        if span.width < 2:
            continue

        table_row = start_row + span.level
        table_col = start_col + span.start_col

        # Resolve styling: defaults < level < label
        props = _merge_with_defaults(
            _merge_with_defaults(default_properties, level_properties.get(span.level)),
            label_properties.get(span.label),
        )

        # Separate property-applier keys from Cell/set kwargs
        text_props = props.pop("text_props", {})
        pad = props.pop("pad", None)
        height_scaling = props.pop("height_scaling", None)
        visible_edges = props.pop("visible_edges", None)
        custom_modifiers = props.pop("custom_modifiers", None)

        span_cell = add_table_multispan_cell(
            table, (table_row, table_col), span.width, 1, text=span.label, **props
        )

        if text_props:
            span_cell.set_text_props(**text_props)
        if pad is not None:
            span_cell.PAD = pad
        if visible_edges is not None:
            span_cell.visible_edges = visible_edges
        if height_scaling is not None:
            for col_offset in range(span.width):
                cell = table.get_celld().get((table_row, table_col + col_offset))
                if cell is not None:
                    cell.set_height(cell.get_height() * height_scaling)
        if custom_modifiers:
            for modifier in _ensure_list(custom_modifiers):
                modifier(span_cell)

        span_cells.append(span_cell)

    return span_cells
