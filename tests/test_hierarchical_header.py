import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import pytest

from mpltablelayers import SpanCell, add_hierarchical_header

matplotlib.use("Agg")


@pytest.fixture
def table_for_header():
    """A table with enough rows for a 2-level header + data."""
    fig, ax = plt.subplots()
    table = ax.table(cellText=[[""] * 4] * 4, loc="center")
    yield table
    plt.close(fig)


class TestAddHierarchicalHeader:
    def test_creates_span_cells(self, table_for_header):
        idx = pd.MultiIndex.from_tuples([
            ("A", "x"), ("A", "y"), ("B", "x"), ("B", "y"),
        ])
        spans = add_hierarchical_header(table_for_header, idx)
        assert len(spans) == 2
        assert all(isinstance(s, SpanCell) for s in spans)

    def test_span_labels(self, table_for_header):
        idx = pd.MultiIndex.from_tuples([
            ("A", "x"), ("A", "y"), ("B", "x"), ("B", "y"),
        ])
        spans = add_hierarchical_header(table_for_header, idx)
        labels = [s.get_text().get_text() for s in spans]
        assert labels == ["A", "B"]

    def test_single_level_no_spans(self, table_for_header):
        idx = pd.Index(["A", "B", "C", "D"])
        spans = add_hierarchical_header(table_for_header, idx)
        assert spans == []

    def test_default_properties(self, table_for_header):
        idx = pd.MultiIndex.from_tuples([("A", "x"), ("A", "y"), ("B", "z"), ("B", "w")])
        spans = add_hierarchical_header(
            table_for_header, idx,
            default_properties={"facecolor": "red"},
        )
        red = matplotlib.colors.to_rgba("red")
        for span in spans:
            assert span.get_facecolor() == red

    def test_level_properties(self, table_for_header):
        idx = pd.MultiIndex.from_tuples([("A", "x"), ("A", "y"), ("B", "z"), ("B", "w")])
        spans = add_hierarchical_header(
            table_for_header, idx,
            level_properties={0: {"facecolor": "blue"}},
        )
        blue = matplotlib.colors.to_rgba("blue")
        for span in spans:
            assert span.get_facecolor() == blue

    def test_label_properties_override(self, table_for_header):
        idx = pd.MultiIndex.from_tuples([("A", "x"), ("A", "y"), ("B", "z"), ("B", "w")])
        spans = add_hierarchical_header(
            table_for_header, idx,
            default_properties={"facecolor": "red"},
            label_properties={"A": {"facecolor": "green"}},
        )
        green = matplotlib.colors.to_rgba("green")
        red = matplotlib.colors.to_rgba("red")
        a_span = [s for s in spans if s.get_text().get_text() == "A"][0]
        b_span = [s for s in spans if s.get_text().get_text() == "B"][0]
        assert a_span.get_facecolor() == green
        assert b_span.get_facecolor() == red

    def test_start_row_offset(self, table_for_header):
        idx = pd.MultiIndex.from_tuples([("A", "x"), ("A", "y"), ("B", "z"), ("B", "w")])
        # start_row=1 means the header starts at table row 1 instead of 0
        spans = add_hierarchical_header(table_for_header, idx, start_row=1)
        assert len(spans) == 2

    def test_text_props(self, table_for_header):
        idx = pd.MultiIndex.from_tuples([("A", "x"), ("A", "y"), ("B", "z"), ("B", "w")])
        spans = add_hierarchical_header(
            table_for_header, idx,
            default_properties={"text_props": {"weight": "bold"}},
        )
        for span in spans:
            assert span.get_text().get_weight() == "bold"

    def test_custom_modifiers(self, table_for_header):
        idx = pd.MultiIndex.from_tuples([("A", "x"), ("A", "y"), ("B", "z"), ("B", "w")])
        called = []
        add_hierarchical_header(
            table_for_header, idx,
            default_properties={"custom_modifiers": [lambda c: called.append(c)]},
        )
        assert len(called) == 2
