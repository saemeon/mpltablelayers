"""Tests for apply_table_*_property helpers."""

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
    fig.canvas.draw()
    yield table
    plt.close(fig)


def test_apply_table_cell_property_facecolor(simple_table):
    mpltablelayers.apply_table_cell_property(simple_table, 0, 0, {"facecolor": "green"})
    cell = simple_table.get_celld()[(0, 0)]
    assert cell.get_facecolor()[:3] == pytest.approx((0.0, 0.5019, 0.0), abs=0.01)


def test_apply_table_row_property_all_cells(simple_table):
    mpltablelayers.apply_table_row_property(simple_table, 1, {"facecolor": "#ff0000"})
    for (r, c), cell in simple_table.get_celld().items():
        if r == 1:
            assert cell.get_facecolor()[:3] == pytest.approx((1.0, 0.0, 0.0), abs=1e-3)


def test_apply_table_col_property_all_cells(simple_table):
    mpltablelayers.apply_table_col_property(simple_table, 0, {"facecolor": "#0000ff"})
    for (r, c), cell in simple_table.get_celld().items():
        if c == 0:
            assert cell.get_facecolor()[:3] == pytest.approx((0.0, 0.0, 1.0), abs=1e-3)


def test_apply_table_range_property(simple_table):
    mpltablelayers.apply_table_range_property(
        simple_table,
        bottom_left=(1, 0),
        top_right=(2, 1),
        property_dict={"facecolor": "yellow"},
    )
    # rows 1 and 2, cols 0 and 1 should be yellow
    for r in (1, 2):
        for c in (0, 1):
            cell = simple_table.get_celld().get((r, c))
            if cell is not None:
                assert cell.get_facecolor()[:3] == pytest.approx(
                    (1.0, 1.0, 0.0), abs=1e-3
                )
