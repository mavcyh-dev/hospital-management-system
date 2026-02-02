from typing import TypeVar, Generic
from collections.abc import Sequence

from app.core.app import App
from app.ui.inputs.base_input import BaseInput
from app.ui.inputs.input_result import InputResult
from app.ui.prompts import prompt_choice, KeyAction
from app.lookups.enums import BaseEnum

E = TypeVar("E", bound="BaseEnum")


class EnumInput(BaseInput, Generic[E]):
    """Input for selecting enum options."""

    def __init__(
        self,
        app: App,
        label: str,
        allowed: Sequence[E],
    ):
        super().__init__(app)
        self.label = label
        self.allowed = list(allowed)
        self._enum_cls = type(allowed[0])

    def prompt(
        self, default: InputResult | None = None, consumed: InputResult | None = None
    ) -> InputResult | KeyAction:
        options = [(enum, enum.display) for enum in self.allowed]

        # Determine default key if provided
        if default:
            default_enum = (
                self._enum_cls(default.value)
                if default.value in [sex.value for sex in self.allowed]
                else None
            )
        else:
            default_enum = None

        selected = prompt_choice(
            message=self.label,
            options=options,
            default=default_enum,
            exitable=True,
            clearable=True,
            scrollable=False,
        )

        if isinstance(selected, KeyAction):
            return selected

        return InputResult(
            value=selected.value if selected is not None else None,
            display_value=selected.display if selected is not None else None,
        )
