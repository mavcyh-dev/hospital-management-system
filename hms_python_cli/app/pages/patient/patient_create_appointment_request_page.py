from typing import Any

from enum import Enum
import time
from sqlalchemy.orm import Session

from app.database.models.user_person import User

from app.ui.utils import app_logo
from app.ui.menu_form import MenuForm, MenuField
from app.ui.inputs.text_input import TextInput
from app.ui.inputs.filter_input import FilterInput, FilterItem
from app.ui.inputs.doctor_by_specialty_input import DoctorBySpecialtyInput
from app.pages.base_page import BasePage


class FieldKey(Enum):
    SPECIALTY = "Specialty"
    REASON = "Reason"
    PREFERRED_DOCTOR = "Preferred Doctor"
    PREFERRED_DATE = "Preferred Date"
    PREFERRED_TIME = "Preferred Time"


class PatientCreateAppointmentRequestPage(BasePage):
    fields: list[MenuField] | None = None

    def run(self) -> BasePage | None:

        self.clear()

        if self.fields is None:
            self.fields = self._init_fields()

        while True:
            menu_form = MenuForm(
                self.fields, "Create Appointment Request", submit_label="Submit"
            )
            data = menu_form.run(self.console)

            if data is None:
                return

            # Attempt adding appointment request
            try:
                with self.app.session_scope() as session:
                    pass
                    self.print_success("Appointment request created successfully!")
                    time.sleep(2)
                    return

            except Exception as e:
                self.print_error(f"Failed to create account: {e}")
                input("Press Enter to continue...")
                continue

    def _init_fields(self) -> list[MenuField]:
        return [
            MenuField(
                FieldKey.SPECIALTY.value,
                FieldKey.SPECIALTY.value,
                FilterInput(
                    self.app,
                    FieldKey.SPECIALTY.value,
                    [
                        FilterItem(value=id, filter_values=[name])
                        for id, name in self.app.lookup_cache.get_all_specialties()
                    ],
                ),
            ),
            MenuField(
                FieldKey.REASON.value,
                FieldKey.REASON.value,
                TextInput(self.app, FieldKey.REASON.value),
            ),
            MenuField(
                FieldKey.PREFERRED_DOCTOR.value,
                f"{FieldKey.PREFERRED_DOCTOR.value} (By {FieldKey.SPECIALTY.value})",
                DoctorBySpecialtyInput(self.app, FieldKey.PREFERRED_DOCTOR.value),
                required=False,
                consumes_key=FieldKey.SPECIALTY.value,
            ),
            MenuField(
                FieldKey.PREFERRED_DATE.value,
                FieldKey.PREFERRED_DATE.value,
                TextInput(self.app, FieldKey.PREFERRED_DATE.value),
                required=False,
            ),
            MenuField(
                FieldKey.PREFERRED_TIME.value,
                f"{FieldKey.PREFERRED_TIME.value} (Date required)",
                TextInput(self.app, FieldKey.PREFERRED_TIME.value),
                required=False,
            ),
        ]
