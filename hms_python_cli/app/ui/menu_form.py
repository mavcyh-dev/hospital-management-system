from typing import Any, cast, TypeVar
from dataclasses import dataclass, field
from prompt_toolkit.formatted_text import FormattedText
from rich.console import Console
from app.ui.input_result import InputResult
from app.ui.inputs.base_input import BaseInput
from app.ui.utils import prompt_choice, KeyAction

T = TypeVar("T")


@dataclass
class MenuField:
    key: str
    label: str
    input: BaseInput
    input_result: InputResult = field(default_factory=lambda: InputResult(value=None))
    required: bool = True
    consumes_key: str | None = None


class MenuForm:
    SUBMIT_OPTION_KEY = "__submit__"

    def __init__(
        self,
        fields: list[MenuField],
        title: str,
        submit_label: str = "Submit",
        default_selected_key: str = "",
    ):
        self.title: str = title
        self.fields = fields
        self.submit_label = submit_label
        self.all_valid: bool
        self.current_key: str = (
            default_selected_key if default_selected_key else fields[0].key
        )

    def run(self, console: Console) -> dict[str, Any] | None:
        self.all_valid = self._all_valid()
        while True:
            console.clear()
            options = self._generate_options()
            selected = prompt_choice(
                message=self.title,
                options=options,
                default=self.current_key,
                exitable=True,
                clearable=False,
                scrollable=False,
                show_frame=True,
            )

            if selected is KeyAction.BACK:
                return None

            if selected == self.SUBMIT_OPTION_KEY:
                if self._all_valid():
                    return {
                        field.key: field.input_result.value for field in self.fields
                    }
                continue

            self.current_key = selected
            field = self._find_field(selected)
            self._edit_field(field)

    def _find_field(self, key: str) -> MenuField:
        return next(i for i in self.fields if i.key == key)

    def _is_valid(self, field: MenuField) -> bool:
        return not (
            field.input_result.error
            or (field.required and field.input_result.value is None)
        )

    def _all_valid(self) -> bool:
        return all(self._is_valid(field) for field in self.fields)

    def _generate_options(self) -> list[tuple[str, FormattedText]]:
        rendered: list[tuple[str, FormattedText]] = []

        for field in self.fields:
            tokens: FormattedText = cast(FormattedText, [])

            if field.input_result.error:
                icon, cls = "✗", "red"
            elif field.input_result.value is not None:
                icon, cls = "✓", "green"
            else:
                icon, cls = "?", "yellow"

            tokens.append((f"class:{cls}", f"[{icon}] "))
            tokens.append((f"class:red", f"{"* " if field.required else "  "}"))
            tokens.append(("class:field", f"{field.label}: "))

            if field.input_result.display_value is not None:
                display = field.input_result.display_value
                cls = "gray"
            elif field.input_result.value is not None:
                display = str(field.input_result.value)
                cls = "gray"
            else:
                display = "[empty]"
                cls = "empty"

            tokens.append((f"class:{cls}", display))

            if field.input_result.error:
                tokens.append(("", "\n    "))
                tokens.append(("class:error", f"→ {field.input_result.error}"))

            rendered.append((field.key, tokens))

        # Submit button
        if self._all_valid():
            rendered.append(
                (
                    self.SUBMIT_OPTION_KEY,
                    cast(FormattedText, [("class:green", f"[{self.submit_label}]")]),
                )
            )

        return rendered

    def _propagate_consumers(
        self, changed_key: str, visited: set[str] | None = None
    ) -> None:
        """Recursively clear input results for fields that depend on changed_key."""
        if visited is None:
            visited = set()

        if changed_key in visited:
            return  # Prevent cycles

        visited.add(changed_key)

        # Find all fields that consume this key
        consumers = [
            field for field in self.fields if field.consumes_key == changed_key
        ]

        for consumer in consumers:
            # Reset the consumer's input
            consumer.input_result = InputResult(value=None)

            # Recursively clear fields that depend on this consumer
            self._propagate_consumers(consumer.key, visited)

    def _edit_field(self, field: MenuField) -> None:
        """Ask the input field for a result, update the MenuField."""
        consumed_field = None
        if field.consumes_key:
            consumed_field = self._find_field(field.consumes_key)
            if consumed_field.input_result.value is None:
                return

        result = field.input.prompt(
            default=field.input_result,
            consumed=consumed_field.input_result if consumed_field else None,
        )
        if result in (KeyAction.LEFT, KeyAction.RIGHT):
            raise ValueError("Scrolling not allowed for menu form inputs!")

        match result:
            case KeyAction.BACK:
                return None
            case KeyAction.CLEAR:
                field.input_result = InputResult(value=None)

        if result.value != field.input_result.value:
            self._propagate_consumers(field.key)
        if result == KeyAction.CLEAR:
            return None

        field.input_result.value = result.value
        field.input_result.display_value = result.display_value
        field.input_result.error = result.error

        if not field.input_result.error:
            index = self.fields.index(field)
            field_count = len(self.fields)
            if self._all_valid() and (index + 1) >= field_count:
                self.current_key = self.SUBMIT_OPTION_KEY
            elif (index + 1) == len(self.fields):
                self.current_key = self.fields[index].key
            else:
                self.current_key = self.fields[index + 1].key
