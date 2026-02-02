from enum import StrEnum

from app.pages.core.base_page import BasePage
from app.ui.inputs.filter_input import FilterInput, FilterItem
from app.ui.menu_form import KeyAction, MenuField, MenuForm


class FieldKey(StrEnum):
    MEDICATION = "Medication"


class AdminSelectMedicationToManage(BasePage):
    @property
    def title(self):
        return "Select medication to manage"

    fields: list[MenuField] | None = None

    def run(self) -> BasePage | None:
        from app.pages.admin.medication.admin_manage_selected_medication_page import (
            AdminManageSelectedMedicationPage,
        )

        if self.fields is None:
            self.fields = self._init_fields()
        menu_form = MenuForm(
            self.fields,
            title="Select medication",
            submit_label="Select",
        )

        while True:
            self.clear()
            self.display_logged_in_header(self.app)
            data = menu_form.run()

            if data is None:
                continue
            if data is KeyAction.BACK:
                return

            return AdminManageSelectedMedicationPage(
                self.app, data[FieldKey.MEDICATION.value]
            )

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
        ]
