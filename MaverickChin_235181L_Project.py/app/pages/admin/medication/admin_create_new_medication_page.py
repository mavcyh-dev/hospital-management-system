from enum import Enum

from app.database.models import Medication
from app.pages.core.base_page import BasePage
from app.ui.inputs.text_input import TextInput
from app.ui.menu_form import KeyAction, MenuField, MenuForm
from app.ui.prompts import prompt_error, prompt_success
from app.validators import (
    validate_medication_generic_name_exists,
)


class FieldKey(Enum):
    GENERIC_NAME = "Generic Name"


class AdminCreateNewMedication(BasePage):
    @property
    def title(self):
        return "Create new medication"

    fields: list[MenuField] | None = None

    def run(self) -> BasePage | None:
        if self.fields is None:
            self.fields = self._init_fields()
        menu_form = MenuForm(self.fields, "Medication details", submit_label="Create")

        while True:
            self.clear()
            self.display_logged_in_header(self.app)
            data = menu_form.run()

            if data is None:
                continue
            if data is KeyAction.BACK:
                return

            # Attempt adding new medication
            try:
                with self.app.session_scope() as session:
                    new_medication = Medication(
                        generic_name=data[FieldKey.GENERIC_NAME.value]
                    )
                    self.app.repos.medication.add(session, new_medication)
                    prompt_success(self.console, "New medication created successfully!")
                    return

            except Exception as e:
                prompt_error(self.console, f"Failed to create new medication: {e}")
                continue

    def _init_fields(self) -> list[MenuField]:
        return [
            MenuField(
                FieldKey.GENERIC_NAME.value,
                FieldKey.GENERIC_NAME.value,
                TextInput(
                    self.app,
                    FieldKey.GENERIC_NAME.value,
                    validators=[
                        lambda x: validate_medication_generic_name_exists(
                            x, self.app.session_scope, self.app.repos.medication
                        ),
                    ],
                ),
            ),
        ]
