from enum import Enum

from app.core.app import App
from app.pages.core.base_page import BasePage
from app.ui.inputs.filter_input import FilterInput, FilterItem
from app.ui.inputs.text_input import TextInput
from app.ui.menu_form import KeyAction, MenuField, MenuForm
from app.ui.prompts import prompt_error, prompt_success


class FieldKey(Enum):
    MEDICATION = "Medication"
    INSTRUCTIONS = "Instructions"


class DoctorCreatePrescriptionItemPage(BasePage):
    fields: list[MenuField] | None = None

    def __init__(
        self,
        app: App,
        *,
        prescription_id: int | None = None,
        appointment_id: int | None = None,
    ):
        super().__init__(app)
        self.prescription_id = prescription_id
        self.appointment_id = appointment_id

    def run(self) -> BasePage | None:
        if (self.prescription_id is not None and self.appointment_id is not None) or (
            self.prescription_id is None and self.appointment_id is None
        ):
            raise ValueError(
                "DoctorCreatePrescriptionItemPage should only receive either the prescription_id, or appointment_id if there is not prescription yet."
            )

        if self.prescription_id is not None:
            with self.app.session_scope() as session:
                prescription = self.app.repos.prescription.get(
                    session, self.prescription_id
                )
                if prescription is None:
                    raise ValueError(
                        f"Prescription item {self.prescription_id} does not exist."
                    )
                self.prescription = prescription

        if self.fields is None:
            self.fields = self._init_fields()
        menu_form = MenuForm(
            self.fields,
            "Create new prescription item",
            submit_label="Create",
        )

        while True:
            self.clear()
            self.display_user_header(self.app)
            data = menu_form.run()

            if data is None:
                continue
            if data is KeyAction.BACK:
                return

            # Attempt prescription item creation
            try:
                with self.app.session_scope() as session:
                    if self.appointment_id is not None:
                        prescription = self.app.repos.prescription.add_prescription_for_appointment_id(
                            session, self.appointment_id
                        )
                        self.prescription = prescription
                    self.app.repos.prescription.add_prescription_item(
                        session,
                        prescription_id=self.prescription.prescription_id,
                        medication_id=data[FieldKey.MEDICATION.value],
                        instructions=data[FieldKey.INSTRUCTIONS.value],
                    )
                    prompt_success(
                        self.console,
                        "Prescription item created successfully.",
                    )
                    return
            except Exception as e:
                prompt_error(self.console, f"Failed to create prescription item: {e}")
                continue

    def _init_fields(self) -> list[MenuField]:
        with self.app.session_scope() as session:
            medications = self.app.repos.medication.get_all(session)

        return [
            MenuField(
                FieldKey.MEDICATION.value,
                FieldKey.MEDICATION.value,
                FilterInput(
                    self.app,
                    FieldKey.MEDICATION.value,
                    [
                        FilterItem(med.medication_id, [med.generic_name])
                        for med in medications
                    ],
                ),
            ),
            MenuField(
                FieldKey.INSTRUCTIONS.value,
                FieldKey.INSTRUCTIONS.value,
                TextInput(self.app, FieldKey.INSTRUCTIONS.value),
                required=False,
            ),
        ]
