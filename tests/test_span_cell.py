"""Tests for SpanCell and add_table_multispan_cell."""

import matplotlib
import matplotlib.pyplot as plt
import pytest

import mpltablelayers

matplotlib.use("Agg")


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
