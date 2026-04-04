"""Module containing util functions."""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from enum import Enum, EnumMeta
from typing import Any

from matplotlib.figure import Figure
from matplotlib.text import Text
from matplotlib.transforms import Bbox


def flatten_list_of_lists(list_of_lists):
    """Flatten a passed list."""
    flat_list = []
    for list in list_of_lists:
        flat_list += list
    return flat_list


def available_kw(fun: Callable) -> list[str]:
    """Get list of parameters a function takes.

    Parameters
    ----------
    fun : Callable
        some function

    Returns
    -------
    list[str]
        list of parameter names function fun takes
    """
    return list(inspect.signature(fun).parameters)


def filter_kw(kw_list: list[str], **kwargs) -> dict[str, Any]:
    """Filter keyword_list from kwargs, ie reduce dict to desired set of keywords.

    Parameters
    ----------
    kw_list : list[str]
        List of keywords.

    **kwargs:
        keyword arguments to filter.

    Returns
    -------
    dict[str, Any]
        Dict with all key, value pairs from kwargs with key in kw_list.
    """
    return {key: kwargs[key] for key in kw_list if key in kwargs}


def filtered_call(func):
    """Call a function with filtered kw."""

    def wrapper(**kwargs):
        func(**filter_kw(available_kw(func), **kwargs))

    return wrapper


def separate_kwargs(
    functions: list[Callable],
    **kwargs,
) -> tuple[dict[str, Any], ...]:
    """Separate keyword arguments into those accepted by each function.

    This allows mapping pooled kwargs to a list of functions.

    Parameters
    ----------
    functions : list[Callable]
        functions to assign keywords to.
    **kwargs:
        keyword arguments to separate

    Returns
    -------
    tuple[dict[str, Any], ...]
        Tuple with separated keyword arguments, one kwargs per function.
            **fun0_kwargs for functions[0],
            ...
            **funn_kwargs for functions[n],
            ...
            **rest_kwargs = remaining kwargs
    """
    separated_kwargs = []
    for func in functions:
        separated_kwargs.append(filter_kw(available_kw(func), **kwargs))

    rest_kwargs = {
        key: kwargs[key]
        for key in kwargs
        if key not in flatten_list_of_lists(separated_kwargs)
    }

    return *separated_kwargs, rest_kwargs


class ExtendedBbox(Bbox):
    """Bbox extended with width and height in inches."""

    width_inch: float
    """The (signed) width of the bounding box in inches."""

    height_inch: float
    """The (signed) height of the bounding box in inches."""


def get_text_bbox(
    text: str | Text | None = None,
    fig: Figure | None = None,
    fontsize: float = 8,
    update_from: Text | None = None,
    **kwargs,
) -> ExtendedBbox:
    """
    Measure the rendered bounding box of a text element.

    The returned bbox is extended with:

    - `width_inch`
    - `height_inch`

    Parameters
    ----------
    text : str | Text | None
        Text content or existing `Text` artist to measure.

        - If `text` is a string, a temporary `Text` artist is created.
        - If `text` is already a `Text` instance, it is measured directly.
        - If `text` is None, a zero-sized bbox is returned.

    fig : Figure | None, optional
    fontsize : float, default 8
    update_from : Text | None, optional
        Optional `Text` object whose properties are copied to the
        temporary text artist before measurement.
    **kwargs
        Additional keyword arguments forwarded to `Figure.text()` when
        creating a temporary text artist.

    Returns
    -------
    ExtendedBbox
        Bounding box in display units with additional attributes
        `width_inch` and `height_inch`.
    """
    if text is None:
        text_box = Bbox([[0, 0], [0, 0]])
        text_box.width_inch = 0
        text_box.height_inch = 0
        return text_box

    if isinstance(text, Text):
        text_element = text
        fig = text_element.figure
        remove_text = False
    else:
        fig = fig or Figure()
        text_element = fig.text(0.5, 0.5, text, fontsize=fontsize, **kwargs)
        if update_from is not None:
            text_element.update_from(update_from)
        remove_text = True
    try:
        renderer = fig.canvas.get_renderer() if fig.canvas else None
    except Exception:
        renderer = None

    text_box = text_element.get_window_extent(renderer=renderer)

    if remove_text:
        text_element.remove()
    text_box.width_inch = text_box.width / fig.get_dpi()
    text_box.height_inch = text_box.height / fig.get_dpi()
    return text_box


class PrintableEnumMeta(EnumMeta):
    """Metaclass to make enum repr return a list of all elements."""

    def __repr__(cls) -> str:
        """Repr returning a string with all members of the enum."""
        return (
            cls.__doc__ + "\n" + "\n".join([f"{key}" for key in cls.__members__.keys()])
        )

    def __getitem__(cls, item: str) -> tuple[float, float]:
        """Get element of enum.

        Prints available members KeyError.
        """
        item = item.replace("-", "_")  # ensure backward compatibility
        try:
            return cls._member_map_[item]
        except KeyError:
            raise KeyError(
                f"'{item}' is not a member of {cls.__name__}. "
                "available members: "
                + ", ".join([f"{key}" for key in cls.__members__.keys()])
            )


class PrintableEnum(Enum, metaclass=PrintableEnumMeta):
    """Make enums print members by inheriting from this class instead of enum."""

    ...


def strip_lang_suffix(input_string: str, fallback="en") -> tuple[str, str]:
    """Split language suffix (_de, _en, _it, _fr) from input string.

    Parameters
    ----------
    input_string : str

    Returns
    -------
    tuple
        - The stripped string (without the language suffix).
        - The language code (e.g., 'de', 'en', 'it', 'fr')
          if a suffix was found, or None if not.

    Examples
    --------
    - `strip_lang_suffix("example_de")`  # Output: ("example", "de")
    - `strip_lang_suffix("example_en")`  # Output: ("example", "en")
    - `strip_lang_suffix("example")`     # Output: ("example", "en"),
      since "en" is set as fallback
    """
    # Define possible suffixes
    suffixes = ["_de", "_en", "_it", "_fr"]

    # Iterate over the suffixes to check if any is at the end of the input string
    for suffix in suffixes:
        if input_string.endswith(suffix):
            # Return the stripped string and the language code
            stripped_string = input_string[: -len(suffix)]
            lang = suffix[1:]  # Extract the language code (remove the underscore)
            return stripped_string, lang

    return input_string, fallback


# Explicit LaTeX commands that require `usetex=True`
_LATEX_UNSUPPORTED_COMMANDS = {
    # text mode
    r"\text",
    r"\textbf",
    r"\textit",
    r"\textrm",
    r"\textsf",
    r"\texttt",
    r"\textsc",
    r"\textmd",
    r"\textnormal",
    # font size / font selection
    r"\fontsize",
    r"\selectfont",
    r"\tiny",
    r"\scriptsize",
    r"\footnotesize",
    r"\small",
    r"\normalsize",
    r"\large",
    r"\Large",
    r"\LARGE",
    r"\huge",
    r"\Huge",
    # document structure
    r"\documentclass",
    r"\usepackage",
    r"\RequirePackage",
    r"\begin",
    r"\end",
    # macro definitions
    r"\newcommand",
    r"\renewcommand",
    r"\providecommand",
    r"\newenvironment",
    r"\renewenvironment",
    # spacing / layout
    r"\hspace",
    r"\vspace",
    r"\addvspace",
    r"\noindent",
    r"\parbox",
    r"\minipage",
    # colour (requires xcolor)
    r"\textcolor",
    r"\color",
    r"\definecolor",
    # references / labels
    r"\label",
    r"\ref",
    r"\pageref",
    r"\cite",
    # alignment environments
    r"\align",
    r"\align*",
    # r"\equation", # may be part of a string
    r"\equation*",
    r"\gather",
    r"\multline",
    # font switches
    r"\bfseries",
    r"\itshape",
    r"\scshape",
    r"\mdseries",
    r"\rmfamily",
    r"\sffamily",
    r"\ttfamily",
}


def requires_usetex(text: str | None) -> bool:
    """Return True if the string contains LaTeX commands.

    Checks for commands that likely require ``usetex=True``.
    """
    if not text:
        return False

    for cmd in _LATEX_UNSUPPORTED_COMMANDS:
        if cmd in text:
            return True

    return False


def _patch_method(set_obj, get_obj, set_name: str, get_name: str | None = None) -> None:
    """Bind a method from one object/class to another object.

    Parameters
    ----------
    set_obj : object
        Object to patch (e.g. ``fig`` or ``ax``).
    get_obj : type
        Class to retrieve the method from (e.g. ``SNBFigure`` or ``SNBAxes``).
    set_name : str
        Attribute name to set on ``set_obj`` (e.g. ``'set_title'``).
    get_name : str, optional
        Method name to retrieve from ``get_obj``.
        Defaults to ``set_name`` if not provided.

    Notes
    -----
    ``__get__(instance, owner)`` invokes the descriptor protocol,
    binding the unbound method to ``set_obj`` as if it were defined
    on ``type(set_obj)``. This correctly handles all descriptor types
    (plain functions, classmethods, etc.) and is the mechanism Python
    itself uses internally when accessing methods on an instance.
    """
    if get_name is None:
        get_name = set_name
    setattr(
        set_obj, set_name, getattr(get_obj, get_name).__get__(set_obj, type(set_obj))
    )


class MethodProxy:
    """Proxy that forwards method calls to a specified class.

    Passes a given instance as self.

    This allows calling methods of a parent or sibling class on an instance,
    bypassing any overrides defined on the instance's own class.

    Parameters
    ----------
    instance : object
        The instance to pass as ``self`` to the proxied methods.
    cls : type
        The class whose methods are proxied.

    Examples
    --------
    >>> proxy = MethodProxy(fig, matplotlib.figure.Figure)
    >>> proxy.legend()   # calls Figure.legend(fig, ...)
    >>> proxy.subplots() # calls Figure.subplots(fig, ...)
    """

    def __init__(self, instance: object, cls: type) -> None:
        self._instance = instance
        self._cls = cls

    def __getattr__(self, name: str) -> functools.partial[Any]:
        """Look up ``name`` on the proxied class.

        Return it bound to the wrapped instance.
        """
        return functools.partial(getattr(self._cls, name), self._instance)
