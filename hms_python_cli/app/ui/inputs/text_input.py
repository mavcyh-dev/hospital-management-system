from collections.abc import Callable
from typing import Any, Sequence

from app.core.app import App
from app.ui.inputs.base_input import BaseInput
from app.ui.inputs.input_result import InputResult
from app.ui.prompts import KeyAction, prompt_text

Validator = Callable[[Any], InputResult]


class TextInput(BaseInput):
    """Generic text input. Can run multiple validators in order."""

    def __init__(
        self,
        app: App,
        label: str,
        validators: Validator | Sequence[Validator] | None = None,
        is_password: bool = False,
    ):
        super().__init__(app)
        self.label = label
        self.is_password = is_password

        # Normalize to a list
        if validators is None:
            self.validators: list[Validator] = []
        elif callable(validators):
            # Single validator -> wrap in list
            self.validators = [validators]
        else:
            # Sequence of validators
            self.validators = list(validators)

    def prompt(
        self, default: InputResult | None = None, consumed: InputResult | None = None
    ) -> InputResult | KeyAction:
        if self.is_password or default is None:
            default_string = ""
        elif default.display_value is not None:
            default_string = default.display_value
        elif default.value is not None:
            default_string = str(default.value)
        else:
            default_string = ""
        raw = prompt_text(
            self.label,
            is_password=self.is_password,
            default=default_string,
            exitable=True,
            clearable=True,
        )

        if isinstance(raw, KeyAction):
            return raw

        if not self.is_password:
            raw = raw.strip()
        if len(raw) == 0:
            return InputResult(value=None)

        # Run validators in order
        last_result: InputResult | None = None
        for validator in self.validators:
            last_result = validator(raw if last_result is None else last_result.value)
            if last_result.error is not None:
                # Stop on first error
                break

        # Perform password masking with "*"
        if self.is_password:
            if last_result is not None:
                return InputResult(
                    value=last_result.value,
                    display_value=len(last_result.value) * "*",
                    error=last_result.error,
                )
            else:
                return InputResult(
                    value=raw,
                    display_value=len(raw) * "*",
                )

        # Return result from last validator, or raw if no validators
        return last_result if last_result is not None else InputResult(value=raw)
