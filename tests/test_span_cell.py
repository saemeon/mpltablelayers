"""Tests for SpanCell and add_table_multispan_cell."""

import matplotlib
import matplotlib.pyplot as plt
import pytest

import mpltablelayers
from mpltablelayers import SpanCell, add_table_multispan_cell

matplotlib.use("Agg")


@pytest.fixture
def table_and_fig():
    fig, ax = plt.subplots()
    table = ax.table(cellText=[["a", "b", "c"]] * 3, loc="center")
    yield table, fig
    plt.close(fig)


@pytest.fixture
def simple_table():
    fig, ax = plt.subplots()
    ax.axis("off")
    table = ax.table(
        cellText=[["a", "b"], ["c", "d"]],
        colLabels=["X", "Y"],
        loc="center",
    )
    table.scale(1, 1.5)
    fig.canvas.draw()
    yield table
    plt.close(fig)


class TestSpanCell:
    def test_is_cell_subclass(self, table_and_fig):
        table, _ = table_and_fig
        span = add_table_multispan_cell(table, (2, 0), 2, 1)
        assert isinstance(span, SpanCell)

    def test_update_bounds_on_anchor_move(self, table_and_fig):
        table, _ = table_and_fig
        span = add_table_multispan_cell(table, (2, 0), 2, 1)
        cell = table.get_celld()[(2, 0)]
        cell.set_x(0.5)
        assert span.get_x() == 0.5

    def test_update_bounds_on_anchor_resize(self, table_and_fig):
        table, _ = table_and_fig
        span = add_table_multispan_cell(table, (2, 0), 2, 1)
        cell = table.get_celld()[(2, 1)]
        original_width = span.get_width()
        cell.set_width(cell.get_width() * 2)
        assert span.get_width() != original_width

    def test_facecolor(self, table_and_fig):
        table, _ = table_and_fig
        span = add_table_multispan_cell(table, (2, 0), 2, 1, facecolor="red")
        assert span.get_facecolor() == matplotlib.colors.to_rgba("red")

    def test_default_zorder(self, table_and_fig):
        table, _ = table_and_fig
        span = add_table_multispan_cell(table, (2, 0), 2, 1)
        assert span.get_zorder() == -1

    def test_custom_zorder(self, table_and_fig):
        table, _ = table_and_fig
        span = add_table_multispan_cell(table, (2, 0), 2, 1, zorder=5)
        assert span.get_zorder() == 5

    def test_text(self, table_and_fig):
        table, _ = table_and_fig
        span = add_table_multispan_cell(table, (2, 0), 2, 1, text="hello")
        assert span.get_text().get_text() == "hello"

    def test_multirow_span(self, table_and_fig):
        table, _ = table_and_fig
        span = add_table_multispan_cell(table, (2, 0), 2, 2)
        assert isinstance(span, SpanCell)


def test_add_table_multispan_cell_returns_span_cell(simple_table):
    span = mpltablelayers.add_table_multispan_cell(
        simple_table, y0x0=(1, 0), width=2, height=1, facecolor="#aabbcc"
    )
    assert isinstance(span, mpltablelayers.SpanCell)


def test_span_cell_facecolor(simple_table):
    span = mpltablelayers.add_table_multispan_cell(
        simple_table, y0x0=(1, 0), width=2, height=1, facecolor="red"
    )
    assert span.get_facecolor()[:3] == pytest.approx((1.0, 0.0, 0.0), abs=1e-3)


def test_span_cell_tracks_anchor_position(simple_table):
    span = mpltablelayers.add_table_multispan_cell(
        simple_table, y0x0=(1, 0), width=2, height=1
    )
    x_before = span.get_x()
    # Move the anchor cell; the span should follow.
    anchor = simple_table.get_celld()[(1, 0)]
    anchor.set_x(anchor.get_x() + 0.1)
    assert span.get_x() == pytest.approx(x_before + 0.1, abs=1e-6)


def test_span_cell_width_covers_two_columns(simple_table):
    span = mpltablelayers.add_table_multispan_cell(
        simple_table, y0x0=(1, 0), width=2, height=1
    )
    cell0 = simple_table.get_celld()[(1, 0)]
    cell1 = simple_table.get_celld()[(1, 1)]
    expected_width = cell0.get_width() + cell1.get_width()
    assert span.get_width() == pytest.approx(expected_width, rel=1e-3)
