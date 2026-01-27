from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, TypeVar, cast

from app.ui.inputs.base_input import BaseInput
from app.ui.inputs.input_result import InputResult
from app.ui.prompts import KeyAction, prompt_choice
from prompt_toolkit.formatted_text import FormattedText

T = TypeVar("T")


class MenuFormAction(Enum):
    DELETE = "__delete__"


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
    DELETE_OPTION_KEY = "__delete__"

    def __init__(
        self,
        fields: list[MenuField],
        title: str,
        submit_label: str = "Submit",
        default_selected_key: str = "",
        enable_delete: bool = False,
        delete_label: str = "Delete",
    ):
        self.title: str = title
        self.fields = fields
        self.submit_label = submit_label
        self.all_valid: bool
        self.current_key: str = (
            default_selected_key if default_selected_key else fields[0].key
        )
        self.enable_delete = enable_delete
        self.delete_label = delete_label

    def run(
        self,
    ) -> dict[str, Any] | Literal[KeyAction.BACK] | None:
        self.all_valid = self._all_valid()
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
            return KeyAction.BACK

        if selected == self.SUBMIT_OPTION_KEY:
            if self._all_valid():
                # returns data
                return {field.key: field.input_result.value for field in self.fields}
            return
        if selected == self.DELETE_OPTION_KEY:
            return {MenuFormAction.DELETE.value: MenuFormAction.DELETE}

        self.current_key = selected
        field = self._find_field(selected)
        self._edit_field(field)
        return

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

        for fld in self.fields:
            tokens: FormattedText = cast(FormattedText, [])

            if fld.input_result.error:
                icon, cls = "✗", "red"
            elif fld.input_result.value is not None:
                icon, cls = "✓", "green"
            else:
                icon, cls = "?", "yellow"

            tokens.append((f"class:{cls}", f"[{icon}] "))
            tokens.append(("class:red", f"{"* " if fld.required else "  "}"))
            tokens.append(("class:field", f"{fld.label}: "))

            if fld.input_result.display_value is not None:
                display = fld.input_result.display_value
                cls = "gray"
            elif fld.input_result.value is not None:
                display = str(fld.input_result.value)
                cls = "gray"
            else:
                display = "[empty]"
                cls = "empty"

            tokens.append((f"class:{cls}", display))

            if fld.input_result.error:
                tokens.append(("", "\n    "))
                tokens.append(("class:error", f"→ {fld.input_result.error}"))

            rendered.append((fld.key, tokens))

        # Submit button
        if self._all_valid():
            rendered.append(
                (
                    self.SUBMIT_OPTION_KEY,
                    cast(FormattedText, [("class:green", f"[{self.submit_label}]")]),
                )
            )
        # Delete button
        if self.enable_delete:
            rendered.append(
                (
                    self.DELETE_OPTION_KEY,
                    cast(FormattedText, [("class:red", f"[{self.delete_label}]")]),
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
                return
            case KeyAction.CLEAR:
                field.input_result = InputResult(value=None)

        if result.value != field.input_result.value:
            self._propagate_consumers(field.key)
        if result == KeyAction.CLEAR:
            return

        field.input_result.value = result.value
        field.input_result.display_value = result.display_value
        field.input_result.error = result.error

        if not field.input_result.error:
            index = self.fields.index(field)
            field_count = len(self.fields)
            if self._all_valid():
                if (index + 1) >= field_count:
                    self.current_key = self.SUBMIT_OPTION_KEY
            elif (index + 1) == len(self.fields):
                self.current_key = self.fields[index].key
            else:
                self.current_key = self.fields[index + 1].key
