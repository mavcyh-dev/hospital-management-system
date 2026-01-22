from abc import ABC, abstractmethod

from app.core.app import App
from app.ui.input_result import InputResult
from app.ui.utils import KeyAction


class BaseInput(ABC):
    """Abstract base class for any input field in MenuForm."""

    def __init__(self, app: App):
        self.app = app
        self.console = app.console

    @abstractmethod
    def prompt(
        self, default: InputResult | None, consumed: InputResult | None
    ) -> InputResult | KeyAction:
        """Prompt the user for input and return an InputResult.
        Must return:
            value: the underlying value
            display_value: optional user-friendly display string
            error: optional validation error
        """
        pass
