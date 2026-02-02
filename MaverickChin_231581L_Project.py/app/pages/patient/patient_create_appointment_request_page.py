from datetime import date, datetime, time, timedelta
from enum import Enum

from app.core.config import AppConfig
from app.database.models import Specialty
from app.pages.core.base_page import BasePage
from app.ui.inputs.doctor_by_specialty_input import DoctorBySpecialtyInput
from app.ui.inputs.filter_input import FilterInput, FilterItem
from app.ui.inputs.text_input import TextInput
from app.ui.menu_form import KeyAction, MenuField, MenuForm
from app.ui.prompts import prompt_error, prompt_success
from app.validators import (
    validate_date,
    validate_date_in_range,
    validate_time,
    validate_time_interval,
)


class FieldKey(Enum):
    SPECIALTY = "Specialty"
    REASON = "Reason"
    PREFERRED_DOCTOR = "Preferred Doctor"
    PREFERRED_DATE = "Preferred Date"
    PREFERRED_TIME = "Preferred Time"


class PatientCreateAppointmentRequestPage(BasePage):
    @property
    def title(self):
        return "Create appointment request"

    fields: list[MenuField] | None = None

    def run(self) -> BasePage | None:
        if self.fields is None:
            self.fields = self._init_fields()
        menu_form = MenuForm(
            self.fields, "Create Appointment Request", submit_label="Submit"
        )

        while True:
            self.clear()
            self.display_logged_in_header(self.app)
            data = menu_form.run()

            if data is None:
                continue
            if data is KeyAction.BACK:
                return

            # Attempt adding appointment request
            try:
                with self.app.session_scope() as session:
                    assert self.app.current_person is not None

                    preferred_datetime = None
                    preferred_date = data[FieldKey.PREFERRED_DATE.value]
                    preferred_time = data[FieldKey.PREFERRED_TIME.value]
                    if preferred_date and preferred_time:
                        preferred_datetime = datetime.combine(
                            preferred_date, preferred_time
                        )
                    elif preferred_date:
                        preferred_datetime = datetime.combine(preferred_date, time.min)

                    self.app.services.appointment.create_appointment_request(
                        session=session,
                        patient_profile_id=self.app.current_person.profile_id,
                        specialty_id=data[FieldKey.SPECIALTY.value],
                        reason=data[FieldKey.REASON.value],
                        preferred_doctor_profile_id=data[
                            FieldKey.PREFERRED_DOCTOR.value
                        ],
                        preferred_datetime=preferred_datetime,
                    )
                    prompt_success(
                        self.console, "Appointment request created successfully!"
                    )
                    return

            except Exception as e:
                prompt_error(self.console, f"Failed to create appointment request: {e}")
                continue

    def _init_fields(self) -> list[MenuField]:
        with self.app.session_scope() as session:
            specialties = self.app.repos.specialty.get_all(
                session, conditions=[Specialty.is_in_service.is_(True)]
            )

        return [
            MenuField(
                FieldKey.SPECIALTY.value,
                FieldKey.SPECIALTY.value,
                FilterInput(
                    self.app,
                    FieldKey.SPECIALTY.value,
                    [
                        FilterItem(value=s.specialty_id, filter_values=[s.name])
                        for s in specialties
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
                    f"{FieldKey.PREFERRED_DATE.value} [YYYY-MM-DD] (<{AppConfig.appointment_preferred_datetime_max_days_from_current} days from today)",
                    validators=[
                        validate_date,
                        lambda x: validate_date_in_range(
                            x,
                            date.today(),
                            date.today()
                            + timedelta(
                                days=AppConfig.appointment_preferred_datetime_max_days_from_current
                            ),
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
                    f"{FieldKey.PREFERRED_TIME.value} [HH:MM], 24HR ({AppConfig.appointment_timeslot_min_interval_minutes}-minute intervals)",
                    validators=[
                        validate_time,
                        lambda x: validate_time_interval(
                            x, AppConfig.appointment_timeslot_min_interval_minutes
                        ),
                    ],
                ),
                required=False,
            ),
        ]
