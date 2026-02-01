from enum import StrEnum

from app.pages.core.base_page import BasePage
from app.ui.inputs.filter_input import FilterInput, FilterItem
from app.ui.menu_form import KeyAction, MenuField, MenuForm


class FieldKey(StrEnum):
    SPECIALTY = "Specialty"


class AdminSelectSpecialtyToManage(BasePage):
    @property
    def title(self):
        return "Select specialty to manage"

    fields: list[MenuField] | None = None

    def run(self) -> BasePage | None:
        from app.pages.admin.specialty.admin_manage_selected_specialty_page import (
            AdminManageSelectedSpecialtyPage,
        )

        if self.fields is None:
            self.fields = self._init_fields()
        menu_form = MenuForm(
            self.fields,
            title="Select specialty",
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

            return AdminManageSelectedSpecialtyPage(
                self.app, data[FieldKey.SPECIALTY.value]
            )

    def _init_fields(self) -> list[MenuField]:
        with self.app.session_scope() as session:
            specialties = self.app.repos.specialty.get_all(session)

        return [
            MenuField(
                FieldKey.SPECIALTY.value,
                FieldKey.SPECIALTY.value,
                FilterInput(
                    self.app,
                    FieldKey.SPECIALTY.value,
                    [
                        FilterItem(specialty.specialty_id, [specialty.name])
                        for specialty in specialties
                    ],
                ),
            ),
        ]
