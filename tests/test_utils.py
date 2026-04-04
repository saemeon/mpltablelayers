from mpltablelayers.utils import available_kw, filter_kw, separate_kwargs


def test_available_kw():
    def func(a, b, c=1):
        pass

    assert available_kw(func) == ["a", "b", "c"]


def test_filter_kw():
    result = filter_kw(["a", "c"], a=1, b=2, c=3)
    assert result == {"a": 1, "c": 3}


def test_filter_kw_missing_keys():
    result = filter_kw(["a", "z"], a=1, b=2)
    assert result == {"a": 1}


def test_separate_kwargs():
    def func_a(x, y):
        pass

    def func_b(y, z):
        pass

    a_kw, b_kw, rest = separate_kwargs([func_a, func_b], x=1, y=2, z=3, w=4)
    assert a_kw == {"x": 1, "y": 2}
    assert b_kw == {"y": 2, "z": 3}
    assert rest == {"w": 4}
