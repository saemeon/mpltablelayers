"""Utility functions for mpltablelayers."""

import inspect
from collections.abc import Callable
from typing import Any


def available_kw(fun: Callable) -> list[str]:
    """Get list of parameter names a function accepts.

    Parameters
    ----------
    fun : Callable

    Returns
    -------
    list[str]
        Parameter names.
    """
    return list(inspect.signature(fun).parameters)


def filter_kw(kw_list: list[str], **kwargs) -> dict[str, Any]:
    """Return the subset of *kwargs* whose keys appear in *kw_list*.

    Parameters
    ----------
    kw_list : list[str]
        Allowed keyword names.
    **kwargs
        Keyword arguments to filter.

    Returns
    -------
    dict[str, Any]
    """
    return {key: kwargs[key] for key in kw_list if key in kwargs}


def separate_kwargs(
    functions: list[Callable],
    **kwargs,
) -> tuple[dict[str, Any], ...]:
    """Split keyword arguments among several functions by their signatures.

    Each function receives only the kwargs it accepts.  The last element
    of the returned tuple collects any remaining kwargs that no function
    accepted.

    Parameters
    ----------
    functions : list[Callable]
        Functions whose signatures define the accepted keywords.
    **kwargs
        Keyword arguments to distribute.

    Returns
    -------
    tuple[dict[str, Any], ...]
        One dict per function, plus a final dict of unmatched kwargs.
    """
    separated_kwargs = []
    consumed_keys: set[str] = set()
    for func in functions:
        matched = filter_kw(available_kw(func), **kwargs)
        separated_kwargs.append(matched)
        consumed_keys.update(matched)

    rest_kwargs = {key: kwargs[key] for key in kwargs if key not in consumed_keys}
    return *separated_kwargs, rest_kwargs
