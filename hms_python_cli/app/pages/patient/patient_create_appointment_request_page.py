from enum import Enum
import time
from datetime import datetime, date, timedelta
import operator

from app.database.models.user_person import User

from app.ui.utils import app_logo
from app.ui.menu_form import MenuForm, MenuField
from app.ui.inputs.text_input import TextInput
from app.ui.inputs.filter_input import FilterInput, FilterItem
from app.ui.inputs.doctor_by_specialty_input import DoctorBySpecialtyInput
from app.pages.core.base_page import BasePage

from app.validators import validate_date, validate_date_in_range, validate_time


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
                    assert self.app.current_person is not None
                    patient_profile = self.app.repos.patient_profile.get_by_person_id(
                        session, self.app.current_person.person_id
                    )
                    if not patient_profile:
                        raise ValueError(
                            f"Patient profile not found for person id {self.app.current_person.person_id}"
                        )

                    preferred_datetime = None
                    preferred_date = data[FieldKey.PREFERRED_DATE.value]
                    preferred_time = data[FieldKey.PREFERRED_TIME.value]
                    if preferred_date and preferred_time:
                        preferred_datetime = datetime.combine(
                            preferred_date, preferred_time
                        )

                    self.app.services.appointment.create_appointment_request(
                        session=session,
                        patient_profile_id=patient_profile.profile_id,
                        specialty_id=data[FieldKey.SPECIALTY.value],
                        reason=data[FieldKey.REASON.value],
                        preferred_doctor_profile_id=data[
                            FieldKey.PREFERRED_DOCTOR.value
                        ],
                        preferred_datetime=preferred_datetime,
                    )
                    self.print_success("Appointment request created successfully!")
                    time.sleep(2)
                    return

            except Exception as e:
                self.print_error(f"Failed to create appointment request: {e}")
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
                DoctorBySpecialtyInput(self.app),
                required=False,
                consumes_key=FieldKey.SPECIALTY.value,
            ),
            MenuField(
                FieldKey.PREFERRED_DATE.value,
                FieldKey.PREFERRED_DATE.value,
                TextInput(
                    self.app,
                    f"{FieldKey.PREFERRED_DATE.value} [YYYY-MM-DD]",
                    validators=[
                        validate_date,
                        lambda x: validate_date_in_range(
                            x,
                            date.today(),
                            date.today() + timedelta(365),
                            inclusive=False,
                        ),
                    ],
                ),
                required=False,
            ),
            MenuField(
                FieldKey.PREFERRED_TIME.value,
                f"{FieldKey.PREFERRED_TIME.value} (Date required)",
                TextInput(
                    self.app,
                    f"{FieldKey.PREFERRED_TIME.value} [HH:MM], 24HR",
                    validators=validate_time,
                ),
                required=False,
            ),
        ]
