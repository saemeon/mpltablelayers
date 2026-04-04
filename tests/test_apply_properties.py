import matplotlib
import matplotlib.pyplot as plt
import pytest

from mpltablelayers import (
    apply_table_cell_property,
    apply_table_col_property,
    apply_table_property,
    apply_table_range_property,
    apply_table_row_property,
)


@pytest.fixture
def table():
    fig, ax = plt.subplots()
    t = ax.table(cellText=[["a", "b", "c"]] * 3, loc="center")
    yield t
    plt.close(fig)


class TestApplyTableProperty:
    def test_applies_to_all_cells(self, table):
        apply_table_property(table, {"facecolor": "red"})
        red = matplotlib.colors.to_rgba("red")
        for cell in table.get_celld().values():
            assert cell.get_facecolor() == red


class TestApplyTableCellProperty:
    def test_facecolor(self, table):
        apply_table_cell_property(table, 0, 0, {"facecolor": "blue"})
        blue = matplotlib.colors.to_rgba("blue")
        assert table.get_celld()[(0, 0)].get_facecolor() == blue

    def test_text_props(self, table):
        apply_table_cell_property(table, 0, 0, {"text_props": {"weight": "bold"}})
        assert table.get_celld()[(0, 0)].get_text().get_weight() == "bold"

    def test_pad(self, table):
        apply_table_cell_property(table, 0, 0, {"pad": 0.5})
        assert table.get_celld()[(0, 0)].PAD == 0.5

    def test_visible_edges(self, table):
        apply_table_cell_property(table, 0, 0, {"visible_edges": "BL"})
        assert table.get_celld()[(0, 0)].visible_edges == "BL"

    def test_custom_modifiers(self, table):
        called = []
        apply_table_cell_property(
            table, 0, 0, {"custom_modifiers": [lambda c: called.append(True)]}
        )
        assert called == [True]


class TestApplyTableRowProperty:
    def test_applies_to_full_row(self, table):
        apply_table_row_property(table, 1, {"facecolor": "green"})
        green = matplotlib.colors.to_rgba("green")
        for (r, c), cell in table.get_celld().items():
            if r == 1:
                assert cell.get_facecolor() == green


class TestApplyTableColProperty:
    def test_applies_to_full_col(self, table):
        apply_table_col_property(table, 2, {"facecolor": "yellow"})
        yellow = matplotlib.colors.to_rgba("yellow")
        for (r, c), cell in table.get_celld().items():
            if c == 2:
                assert cell.get_facecolor() == yellow


class TestApplyTableRangeProperty:
    def test_applies_to_range(self, table):
        apply_table_range_property(table, (2, 0), (1, 1), {"facecolor": "purple"})
        purple = matplotlib.colors.to_rgba("purple")
        for (r, c), cell in table.get_celld().items():
            if 1 <= r <= 2 and 0 <= c <= 1:
                assert cell.get_facecolor() == purple
