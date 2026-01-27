from enum import Enum

from app.core.app import App
from app.database.models import PrescriptionItem
from app.pages.core.base_page import BasePage
from app.ui.inputs.filter_input import FilterInput, FilterItem
from app.ui.inputs.text_input import TextInput
from app.ui.menu_form import InputResult, KeyAction, MenuField, MenuForm, MenuFormAction
from app.ui.prompts import prompt_error, prompt_success


class FieldKey(Enum):
    MEDICATION = "Medication"
    INSTRUCTIONS = "Instructions"


class DoctorEditPrescriptionItemPage(BasePage):
    fields: list[MenuField] | None = None

    def __init__(
        self,
        app: App,
        prescription_item_id: int,
    ):
        super().__init__(app)
        self.prescription_item_id = prescription_item_id

    def run(self) -> BasePage | None:

        with self.app.session_scope() as session:
            prescription_item = self.app.repos.prescription.get_prescription_item(
                session, self.prescription_item_id
            )
            if prescription_item is None:
                raise ValueError(
                    f"Prescription item {self.prescription_item_id} does not exist."
                )
            self.prescription_item = prescription_item

        if self.fields is None:
            self.fields = self._init_fields()
        menu_form = MenuForm(
            self.fields,
            "Edit prescription item",
            submit_label="Edit",
            enable_delete=True,
        )

        while True:
            self.clear()
            self.display_user_header(self.app)
            data = menu_form.run()

            if data is None:
                continue
            if data is KeyAction.BACK:
                return
            if data == {MenuFormAction.DELETE.value: MenuFormAction.DELETE}:
                assert self.prescription_item_id is not None
                # Attempt prescription item deletion
                try:
                    with self.app.session_scope() as session:
                        self.app.repos.prescription.delete_by_prescription_item_by_id_with_prescription_cleanup(
                            session, self.prescription_item_id
                        )
                        prompt_success(
                            self.console,
                            "Prescription item deleted successfully.",
                        )
                        return

                except Exception as e:
                    prompt_error(
                        self.console, f"Failed to delete prescription item: {e}"
                    )
                    continue

            elif self.prescription_item_id is not None:
                # Attempt prescription item edit
                try:
                    with self.app.session_scope() as session:
                        prescription_item = PrescriptionItem(
                            prescription_item_id=self.prescription_item_id,
                            prescription_id=self.prescription_item.prescription_id,
                            medication_id=data[FieldKey.MEDICATION.value],
                            instructions=data[FieldKey.INSTRUCTIONS.value],
                        )
                        self.app.repos.prescription.update_prescription_item(
                            session, prescription_item=prescription_item
                        )
                        prompt_success(
                            self.console,
                            "Prescription item edited successfully.",
                        )
                        return

                except Exception as e:
                    prompt_error(self.console, f"Failed to edit prescription item: {e}")
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
                InputResult(
                    value=self.prescription_item.medication_id,
                    display_value=self.prescription_item.medication.generic_name,
                ),
            ),
            MenuField(
                FieldKey.INSTRUCTIONS.value,
                FieldKey.INSTRUCTIONS.value,
                TextInput(self.app, FieldKey.INSTRUCTIONS.value),
                InputResult(value=self.prescription_item.instructions),
                required=False,
            ),
        ]
