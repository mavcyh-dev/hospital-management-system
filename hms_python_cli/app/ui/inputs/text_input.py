from collections.abc import Callable
from typing import Sequence


from app.core.app import App
from app.ui.inputs.base_input import BaseInput
from app.ui.input_result import InputResult
from app.ui.utils import prompt_text


Validator = Callable[[str], InputResult]


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
    ) -> InputResult:
        if self.is_password or default is None:
            default_string = ""
        elif default.display_value is not None:
            default_string = default.display_value
        elif default.value is not None:
            default_string = str(default.value)
        else:
            default_string = ""
        raw = prompt_text(
            self.label, is_password=self.is_password, default=default_string
        )

        if raw is None:
            return InputResult(value=None)

        if not self.is_password:
            raw = raw.strip()

        # Run validators in order
        validated_result: InputResult | None = None
        for validator in self.validators:
            result = validator(raw)
            if result.error is not None:
                # Stop on first error
                return result
            raw = result.value
            validated_result = result

        # Perform password masking with "*"
        if self.is_password:
            if validated_result is not None:
                return InputResult(
                    value=validated_result.value,
                    display_value=len(validated_result.value) * "*",
                    error=validated_result.error,
                )
            else:
                return InputResult(
                    value=raw,
                    display_value=len(raw) * "*",
                )

        # Return result from last validator, or raw if no validators
        return (
            validated_result if validated_result is not None else InputResult(value=raw)
        )
