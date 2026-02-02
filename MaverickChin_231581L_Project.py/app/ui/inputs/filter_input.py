from dataclasses import dataclass
from typing import Any, Sequence

from app.core.app import App
from app.ui.inputs.base_input import BaseInput
from app.ui.inputs.input_result import InputResult
from app.ui.prompts import (
    KeyAction,
    prompt_choice,
    prompt_continue_message,
    prompt_text,
)
from rich.panel import Panel
from rich.text import Text


@dataclass(frozen=True)
class FilterItem:
    value: Any
    filter_values: Sequence[str | None]

    @property
    def display(self):
        return self.filter_values[0]


class FilterInput(BaseInput):
    def __init__(self, app: App, label: str, items: Sequence[FilterItem]):
        super().__init__(app)
        self.label = label
        self.items = list(items)

    def prompt(
        self, default: InputResult | None = None, consumed: InputResult | None = None
    ):
        items = self.items

        if not items:
            prompt_continue_message(self.app.console, "No selectable options.")
            return InputResult(value=None)

        while True:
            value_strings_list = []
            for item in items:
                value_string = " | ".join(
                    fv for fv in item.filter_values if fv is not None
                )
                value_strings_list.append(value_string)
            concat_value_strings = ", ".join(value_strings_list)
            concat_text = Text(concat_value_strings)
            concat_text.truncate(5000, overflow="ellipsis")

            filtered = self.items
            if len(self.items) > 20:
                self.console.print(
                    Panel(
                        concat_text,
                        title=f"{self.label} ({len(filtered)})",
                        title_align="left",
                        padding=(1, 1),
                    )
                )
                raw = prompt_text(
                    "Filter by word search (press Enter to select from all)",
                    exitable=True,
                    clearable=True,
                )
                if isinstance(raw, KeyAction):
                    return raw

                query = raw.strip().lower()

                if query:
                    filtered = [
                        item
                        for item in items
                        if any(
                            query in fv.lower()
                            for fv in item.filter_values
                            if fv is not None
                        )
                    ]
                else:
                    filtered = items

                if not filtered:
                    print("No matches. Try again.")
                    continue

                if len(filtered) == 1:
                    only = filtered[0]
                    print(f"\nMatched: {only.display}")
                    result = prompt_choice(
                        message="Match found. Select?",
                        options=[("Y", "Yes"), ("N", "No")],
                        exitable=True,
                        clearable=True,
                        scrollable=False,
                    )

                    if result is None:
                        return InputResult(value=None)

                    match result:
                        case "Y":
                            return InputResult(only.value, only.display)
                        case "N":
                            continue

            selected = prompt_choice(
                message=f"{self.label}",
                options=[
                    (
                        item,
                        " | ".join(fv for fv in item.filter_values if fv is not None),
                    )
                    for item in filtered
                ],
                exitable=True,
                clearable=True,
                scrollable=False,
            )

            if isinstance(selected, KeyAction):
                return selected

            return InputResult(selected.value, selected.display)
