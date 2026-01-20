from __future__ import annotations
from dataclasses import dataclass
from typing import TypeVar, Any, Optional, overload, Literal

from collections.abc import Sequence
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText, HTML, AnyFormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import choice
from prompt_toolkit.styles import Style
from rich.console import Console
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


def get_exit_keybindings() -> KeyBindings:
    kb = KeyBindings()

    @kb.add("c-b")
    def _(event):
        event.app.exit()

    return kb


def prompt_choice_bottom_toolbar(option_count: int, exitable: bool) -> HTML:
    exit_text = " <b>[Ctrl+B]</b> to go back." if exitable else ""
    return HTML(
        f" Press <b>[Up]</b>/<b>[Down]</b>/<b>[1-{min(9, option_count)}]</b> to select, "
        f"<b>[Enter]</b> to confirm.{exit_text}"
    )


@overload
def prompt_choice(
    message: str,
    options: Sequence[tuple[T, AnyFormattedText]],
    *,
    default: T | None = None,
    exitable: Literal[True],
    show_frame: bool = False,
) -> T | None: ...


@overload
def prompt_choice(
    message: str,
    options: Sequence[tuple[T, AnyFormattedText]],
    *,
    default: T | None = None,
    exitable: Literal[False],
    show_frame: bool = False,
) -> T: ...


def prompt_choice(
    message: str,
    options: Sequence[tuple[T, AnyFormattedText]],
    *,
    default: T | None = None,
    exitable: bool = True,
    show_frame: bool = False,
) -> T | None:
    return choice(
        message=HTML(f"<u>{message}</u>"),
        options=options,
        default=default,
        bottom_toolbar=prompt_choice_bottom_toolbar(len(options), exitable),
        key_bindings=get_exit_keybindings() if exitable else None,
        show_frame=show_frame,
        style=PROMPT_STYLE,
    )


def prompt_text_bottom_toolbar() -> HTML:
    return HTML(" <b>[Enter]</b> to confirm. <b>[Ctrl+B]</b> to go back.")


@overload
def prompt_text(
    message: str,
    *,
    is_password: bool = False,
    default: str = "",
    exitable: Literal[True] = True,
) -> str | None: ...


@overload
def prompt_text(
    message: str,
    *,
    is_password: bool = False,
    default: str = "",
    exitable: Literal[False],
) -> str: ...


def prompt_text(
    message: str,
    is_password: bool = False,
    default: str = "",
    exitable: bool = True,
) -> str | None:
    session = PromptSession()
    if default is None:
        default = ""
    return session.prompt(
        HTML(f" <b><u>{message}</u></b>\n > "),
        is_password=is_password,
        default=default if not is_password else "",
        bottom_toolbar=prompt_text_bottom_toolbar(),
        key_bindings=get_exit_keybindings() if exitable else None,
        style=PROMPT_STYLE,
    )
