import matplotlib
import pytest

matplotlib.use("Agg")


@pytest.fixture
def simple_table():
    """A 3-row x 4-col matplotlib table."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    table = ax.table(
        cellText=[["a", "b", "c", "d"]] * 3,
        loc="center",
    )
    yield table
    plt.close(fig)
