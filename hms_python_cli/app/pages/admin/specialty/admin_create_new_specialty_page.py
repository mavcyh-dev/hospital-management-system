from enum import Enum

from app.database.models import Specialty
from app.pages.core.base_page import BasePage
from app.ui.inputs.text_input import TextInput
from app.ui.menu_form import KeyAction, MenuField, MenuForm
from app.ui.prompts import prompt_error, prompt_success
from app.validators import validate_specialty_name_exists


class FieldKey(Enum):
    NAME = "Name"


class AdminCreateNewSpecialty(BasePage):
    @property
    def title(self):
        return "Create new specialty"

    fields: list[MenuField] | None = None

    def run(self) -> BasePage | None:
        if self.fields is None:
            self.fields = self._init_fields()
        menu_form = MenuForm(self.fields, "Specialty details", submit_label="Create")

        while True:
            self.clear()
            self.display_logged_in_header(self.app)
            data = menu_form.run()

            if data is None:
                continue
            if data is KeyAction.BACK:
                return

            # Attempt adding new specialty
            try:
                with self.app.session_scope() as session:
                    new_specialty = Specialty(name=data[FieldKey.NAME.value])
                    self.app.repos.specialty.add(session, new_specialty)
                    prompt_success(self.console, "New specialty created successfully!")
                    return

            except Exception as e:
                prompt_error(self.console, f"Failed to create new specialty: {e}")
                continue

    def _init_fields(self) -> list[MenuField]:
        return [
            MenuField(
                FieldKey.NAME.value,
                FieldKey.NAME.value,
                TextInput(
                    self.app,
                    FieldKey.NAME.value,
                    validators=[
                        lambda x: validate_specialty_name_exists(
                            x, self.app.session_scope, self.app.repos.specialty
                        ),
                    ],
                ),
            ),
        ]
