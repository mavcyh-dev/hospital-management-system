from typing import overload, Literal, TypeVar
from enum import Enum


from collections.abc import Sequence
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML, AnyFormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import choice
from prompt_toolkit.styles import Style
from rich.padding import Padding
from rich.text import Text
import pyfiglet

T = TypeVar("T")

PROMPT_STYLE = Style.from_dict(
    {
        "input": "fg:#00ff00 bg:#000000",
        "green": "fg:#00ff00",
        "yellow": "fg:#ffff00",
        "red": "fg:#ff4444",
        "gray": "fg:#888888",
        "bold": "bold",
        "field": "fg:#bcbcbc",
        "empty": "fg:#444444 italic",
        "error": "fg:#ff3333 italic",
    }
)

app_logo = Padding(
    Text.from_markup(
        pyfiglet.figlet_format("nyp HMS", font="larry3d"), style="dodger_blue2"
    ),
    (0, 1),
)


class KeyAction(Enum):
    BACK = "__back__"
    CLEAR = "__clear__"
    LEFT = "__left__"
    RIGHT = "__right__"


def get_keybindings(
    exitable: bool, clearable: bool, scrollable: bool = False
) -> KeyBindings:
    kb = KeyBindings()

    if exitable:

        @kb.add("c-b")
        def _(event):
            event.app.exit(result=KeyAction.BACK)

    if clearable:

        @kb.add("c-d")
        def _(event):
            event.app.exit(result=KeyAction.CLEAR)

    if scrollable:

        @kb.add("left")
        def _(event):
            event.app.exit(result=KeyAction.LEFT)

        @kb.add("right")
        def _(event):
            event.app.exit(result=KeyAction.RIGHT)

    return kb


def prompt_choice_bottom_toolbar(
    option_count: int, exitable: bool, clearable: bool, scrollable: bool
) -> HTML:
    exit_text = " <b>[Ctrl+B]</b> to go back." if exitable else ""
    clear_text = " <b>[Ctrl+D]</b> to clear input." if clearable else ""
    scrollable_text = " <b>[Left]</b>/<b>[Right]</b> to scroll." if scrollable else ""
    return HTML(
        f" Press <b>[Up]</b>/<b>[Down]</b>/<b>[1-{min(9, option_count)}]</b> to select, "
        f"<b>[Enter]</b> to confirm.{exit_text}{clear_text}{scrollable_text}"
    )


@overload
def prompt_choice(
    message: str,
    options: Sequence[tuple[T, AnyFormattedText]],
    *,
    default: T | None = None,
    exitable: Literal[True],
    clearable: Literal[True],
    scrollable: Literal[True],
    show_frame: bool = False,
) -> T | Literal[KeyAction.BACK, KeyAction.CLEAR, KeyAction.LEFT, KeyAction.RIGHT]: ...


@overload
def prompt_choice(
    message: str,
    options: Sequence[tuple[T, AnyFormattedText]],
    *,
    default: T | None = None,
    exitable: Literal[True],
    clearable: Literal[True],
    scrollable: Literal[False],
    show_frame: bool = False,
) -> T | Literal[KeyAction.BACK, KeyAction.CLEAR]: ...


@overload
def prompt_choice(
    message: str,
    options: Sequence[tuple[T, AnyFormattedText]],
    *,
    default: T | None = None,
    exitable: Literal[True],
    clearable: Literal[False],
    scrollable: Literal[True],
    show_frame: bool = False,
) -> T | Literal[KeyAction.BACK, KeyAction.LEFT, KeyAction.RIGHT]: ...


@overload
def prompt_choice(
    message: str,
    options: Sequence[tuple[T, AnyFormattedText]],
    *,
    default: T | None = None,
    exitable: Literal[True],
    clearable: Literal[False],
    scrollable: Literal[False],
    show_frame: bool = False,
) -> T | Literal[KeyAction.BACK]: ...


@overload
def prompt_choice(
    message: str,
    options: Sequence[tuple[T, AnyFormattedText]],
    *,
    default: T | None = None,
    exitable: Literal[False],
    clearable: Literal[False],
    scrollable: Literal[False],
    show_frame: bool = False,
) -> T: ...


@overload
def prompt_choice(
    message: str,
    options: Sequence[tuple[T, AnyFormattedText]],
    *,
    default: T | None = None,
    exitable: Literal[True],
    clearable: Literal[False],
    scrollable: bool = False,
    show_frame: bool = False,
) -> T | Literal[KeyAction.BACK, KeyAction.LEFT, KeyAction.RIGHT]: ...


def prompt_choice(
    message: str,
    options: Sequence[tuple[T, AnyFormattedText]],
    *,
    default: T | None = None,
    exitable: bool = True,
    clearable: bool = False,
    scrollable: bool = False,
    show_frame: bool = False,
) -> T | KeyAction:
    return choice(
        message=HTML(f"<u>{message}</u>"),
        options=options,
        default=default,
        bottom_toolbar=prompt_choice_bottom_toolbar(
            len(options), exitable, clearable, scrollable
        ),
        key_bindings=get_keybindings(exitable, clearable, scrollable),
        show_frame=show_frame,
        style=PROMPT_STYLE,
    )


def prompt_text_bottom_toolbar(exitable: bool, clearable: bool) -> HTML:
    exit_text = " <b>[Ctrl+B]</b> to go back." if exitable else ""
    clear_text = " <b>[Ctrl+D]</b> to clear input." if clearable else ""
    return HTML(f" <b>[Enter]</b> to confirm.{exit_text}{clear_text}")


@overload
def prompt_text(
    message: str,
    *,
    is_password: bool = False,
    default: str = "",
    exitable: Literal[True],
    clearable: Literal[True],
) -> str | Literal[KeyAction.BACK, KeyAction.CLEAR]: ...


@overload
def prompt_text(
    message: str,
    *,
    is_password: bool = False,
    default: str = "",
    exitable: Literal[True],
    clearable: Literal[False],
) -> str | Literal[KeyAction.BACK]: ...


@overload
def prompt_text(
    message: str,
    *,
    is_password: bool = False,
    default: str = "",
    exitable: Literal[False],
    clearable: Literal[True],
) -> str | Literal[KeyAction.CLEAR]: ...


@overload
def prompt_text(
    message: str,
    *,
    is_password: bool = False,
    default: str = "",
    exitable: Literal[False],
    clearable: Literal[False],
) -> str: ...


def prompt_text(
    message: str,
    is_password: bool = False,
    default: str = "",
    exitable: bool = True,
    clearable: bool = True,
) -> str | KeyAction:
    session = PromptSession()
    if default is None:
        default = ""
    return session.prompt(
        HTML(f" <b><u>{message}</u></b>\n > "),
        is_password=is_password,
        default=default if not is_password else "",
        bottom_toolbar=prompt_text_bottom_toolbar(exitable, clearable),
        key_bindings=get_keybindings(exitable, clearable),
        style=PROMPT_STYLE,
    )
