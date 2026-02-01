from enum import Enum

from app.pages.core.base_page import BasePage
from app.ui.inputs.text_input import TextInput
from app.ui.menu_form import InputResult, KeyAction, MenuField, MenuForm
from app.ui.prompts import prompt_error, prompt_success


class FieldKey(Enum):
    MEDICATION_ALLERGIES = "Medication Allergies"


class PatientEditProfileInformationPage(BasePage):
    @property
    def title(self):
        return "Edit profile information"

    fields: list[MenuField] | None = None

    def run(self) -> BasePage | None:
        assert self.app.current_person is not None
        self.patient_profile_id = self.app.current_person.profile_id

        with self.app.session_scope() as session:
            patient_profile = self.app.repos.patient_profile.get(
                session, self.patient_profile_id
            )
            if patient_profile is None:
                raise ValueError(
                    f"Patient profile {self.patient_profile_id} does not exist."
                )
            self.patient_profile = patient_profile

        if self.fields is None:
            self.fields = self._init_fields()
        menu_form = MenuForm(
            self.fields,
            "Edit profile information",
            submit_label="Edit",
        )

        while True:
            self.clear()
            self.display_logged_in_header(self.app)
            data = menu_form.run()

            if data is None:
                continue
            if data is KeyAction.BACK:
                return

            elif self.patient_profile_id is not None:
                # Attempt profile information edit
                try:
                    with self.app.session_scope() as session:
                        self.app.services.patient.update_profile_information(
                            session,
                            patient_profile_id=self.patient_profile_id,
                            medication_allergies=data[
                                FieldKey.MEDICATION_ALLERGIES.value
                            ],
                        )

                        prompt_success(
                            self.console,
                            "Profile information edited successfully.",
                        )
                        continue

                except Exception as e:
                    prompt_error(
                        self.console, f"Failed to edit profile information: {e}"
                    )
                    continue

    def _init_fields(self) -> list[MenuField]:
        return [
            MenuField(
                FieldKey.MEDICATION_ALLERGIES.value,
                FieldKey.MEDICATION_ALLERGIES.value,
                TextInput(self.app, FieldKey.MEDICATION_ALLERGIES.value),
                InputResult(value=self.patient_profile.medication_allergies),
                required=False,
            ),
        ]
