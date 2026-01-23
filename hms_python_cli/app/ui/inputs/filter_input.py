from dataclasses import dataclass
from typing import Any, Sequence
from collections.abc import Sequence

from rich.panel import Panel

from app.core.app import App
from app.ui.inputs.base_input import BaseInput
from app.ui.inputs.input_result import InputResult
from app.ui.prompts import prompt_choice, prompt_text, KeyAction


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
        if not items:
            raise ValueError("FilterInput requires at least one FilterItem.")
        self.label = label
        self.items = list(items)

    def prompt(
        self, default: InputResult | None = None, consumed: InputResult | None = None
    ):
        items = self.items

        while True:
            value_strings_list = []
            for item in items:
                value_string = " | ".join(
                    fv for fv in item.filter_values if fv is not None
                )
                value_strings_list.append(value_string)
            concat_value_strings = ", ".join(value_strings_list)

            filtered = self.items
            if len(self.items) > 20:
                self.console.print(
                    Panel(
                        concat_value_strings,
                        title=f"[underline]{self.label} ({len(filtered)})[/]",
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
                    return InputResult(value=None)
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
