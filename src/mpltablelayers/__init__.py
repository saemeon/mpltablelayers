# Copyright (c) Simon Niederberger.
# Distributed under the terms of the Modified BSD License.

from .annotations import (
    CellEllipse,
    add_plottable_cell_annotation,
    add_table_arrow_annotation,
    add_table_cell_annotation,
)
from .plottable_compat import add_plottable_multispan_cell
from .table import (
    HeaderSpan,
    SpanCell,
    add_hierarchical_header,
    add_table_multispan_cell,
    apply_table_cell_property,
    apply_table_col_property,
    apply_table_property,
    apply_table_range_property,
    apply_table_row_property,
    make_table,
    resolve_header_spans,
)

__all__ = [
    "CellEllipse",
    "HeaderSpan",
    "SpanCell",
    "add_hierarchical_header",
    "add_plottable_cell_annotation",
    "add_plottable_multispan_cell",
    "add_table_arrow_annotation",
    "add_table_cell_annotation",
    "add_table_multispan_cell",
    "apply_table_cell_property",
    "apply_table_col_property",
    "apply_table_property",
    "apply_table_range_property",
    "apply_table_row_property",
    "make_table",
    "resolve_header_spans",
]
