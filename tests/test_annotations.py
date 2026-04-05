"""Tests for CellEllipse and add_table_cell_annotation."""

import matplotlib
import matplotlib.pyplot as plt
import pytest
from matplotlib.patches import Ellipse

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
    yield table, ax, fig
    plt.close(fig)


def test_add_table_cell_annotation_returns_cell_ellipse(simple_table):
    table, ax, fig = simple_table
    ann = mpltablelayers.add_table_cell_annotation(table, y0x0=(1, 0))
    assert isinstance(ann, mpltablelayers.CellEllipse)


def test_cell_ellipse_is_ellipse_subclass(simple_table):
    table, ax, fig = simple_table
    ann = mpltablelayers.add_table_cell_annotation(table, y0x0=(1, 0))
    assert isinstance(ann, Ellipse)


def test_cell_ellipse_edgecolor(simple_table):
    table, ax, fig = simple_table
    ann = mpltablelayers.add_table_cell_annotation(table, y0x0=(1, 0), edgecolor="blue")
    assert ann.get_edgecolor()[:3] == pytest.approx((0.0, 0.0, 1.0), abs=1e-3)


def test_cell_ellipse_circle_equal_axes(simple_table):
    table, ax, fig = simple_table
    ann = mpltablelayers.add_table_cell_annotation(table, y0x0=(1, 0), circle=True)
    assert ann.get_width() == pytest.approx(ann.get_height(), rel=1e-6)


def test_cell_ellipse_tracks_anchor(simple_table):
    table, ax, fig = simple_table
    ann = mpltablelayers.add_table_cell_annotation(table, y0x0=(1, 0))
    cx_before, _ = ann.get_center()
    anchor = table.get_celld()[(1, 0)]
    anchor.set_x(anchor.get_x() + 0.1)
    cx_after, _ = ann.get_center()
    assert cx_after == pytest.approx(cx_before + 0.05, abs=1e-4)
