import pandas as pd

from mpltablelayers import HeaderSpan, resolve_header_spans


class TestHeaderSpan:
    def test_width(self):
        span = HeaderSpan(level=0, label="A", start_col=1, end_col=3)
        assert span.width == 3

    def test_width_single(self):
        span = HeaderSpan(level=0, label="A", start_col=2, end_col=2)
        assert span.width == 1


class TestResolveSingleLevel:
    def test_single_level_index(self):
        idx = pd.Index(["A", "B", "C"])
        spans, n = resolve_header_spans(idx)
        assert n == 1
        assert len(spans) == 3
        assert all(s.width == 1 for s in spans)
        assert [s.label for s in spans] == ["A", "B", "C"]

    def test_single_level_no_spanning(self):
        idx = pd.Index(["A", "A", "B"])
        spans, n = resolve_header_spans(idx)
        assert n == 1
        # Single-level never spans
        assert len(spans) == 3

    def test_empty_col_skipped(self):
        idx = pd.Index(["A", "_emptycol_0", "B"])
        spans, n = resolve_header_spans(idx)
        assert len(spans) == 2
        assert [s.label for s in spans] == ["A", "B"]


class TestResolveMultiIndex:
    def test_basic_two_level(self):
        idx = pd.MultiIndex.from_tuples(
            [
                ("A", "x"),
                ("A", "y"),
                ("B", "x"),
                ("B", "y"),
            ]
        )
        spans, n = resolve_header_spans(idx)
        assert n == 2

        level0 = [s for s in spans if s.level == 0]
        level1 = [s for s in spans if s.level == 1]

        # Level 0: A spans 0-1, B spans 2-3
        assert len(level0) == 2
        assert level0[0] == HeaderSpan(0, "A", 0, 1)
        assert level0[1] == HeaderSpan(0, "B", 2, 3)

        # Level 1 (lowest): no spanning
        assert len(level1) == 4
        assert all(s.width == 1 for s in level1)

    def test_three_levels(self):
        idx = pd.MultiIndex.from_tuples(
            [
                ("G1", "A", "x"),
                ("G1", "A", "y"),
                ("G1", "B", "x"),
                ("G2", "A", "x"),
                ("G2", "A", "y"),
            ]
        )
        spans, n = resolve_header_spans(idx)
        assert n == 3

        level0 = [s for s in spans if s.level == 0]
        level1 = [s for s in spans if s.level == 1]

        assert level0[0] == HeaderSpan(0, "G1", 0, 2)
        assert level0[1] == HeaderSpan(0, "G2", 3, 4)

        # Level 1: A(0-1), B(2), A(3-4) — parent break prevents merging A across G1/G2
        assert len(level1) == 3
        assert level1[0] == HeaderSpan(1, "A", 0, 1)
        assert level1[1] == HeaderSpan(1, "B", 2, 2)
        assert level1[2] == HeaderSpan(1, "A", 3, 4)

    def test_spanning_disabled(self):
        idx = pd.MultiIndex.from_tuples([("A", "x"), ("A", "y")])
        spans, n = resolve_header_spans(idx, spanning=False)
        assert all(s.width == 1 for s in spans)

    def test_break_span(self):
        idx = pd.MultiIndex.from_tuples(
            [
                ("A", "x"),
                ("A", "y"),
                ("A", "z"),
            ]
        )
        spans, _ = resolve_header_spans(idx, break_span=[("A", "z")])
        level0 = [s for s in spans if s.level == 0]

        # A should be broken into two groups: cols 0-1 and col 2
        assert len(level0) == 2
        assert level0[0] == HeaderSpan(0, "A", 0, 1)
        assert level0[1] == HeaderSpan(0, "A", 2, 2)

    def test_empty_col_does_not_break_span(self):
        idx = pd.MultiIndex.from_tuples(
            [
                ("A", "x"),
                ("_emptycol_0", ""),
                ("A", "y"),
            ]
        )
        spans, _ = resolve_header_spans(idx)
        level0 = [s for s in spans if s.level == 0]

        # A should span across the empty col: cols 0-2
        assert len(level0) == 1
        assert level0[0] == HeaderSpan(0, "A", 0, 2)

    def test_different_labels_no_spanning(self):
        idx = pd.MultiIndex.from_tuples([("A", "x"), ("B", "y"), ("C", "z")])
        spans, _ = resolve_header_spans(idx)
        level0 = [s for s in spans if s.level == 0]
        assert all(s.width == 1 for s in level0)
