import matplotlib
import matplotlib.pyplot as plt
import pytest

from mpltablelayers import SpanCell, add_table_multispan_cell


@pytest.fixture
def table_and_fig():
    fig, ax = plt.subplots()
    table = ax.table(cellText=[["a", "b", "c"]] * 3, loc="center")
    yield table, fig
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
