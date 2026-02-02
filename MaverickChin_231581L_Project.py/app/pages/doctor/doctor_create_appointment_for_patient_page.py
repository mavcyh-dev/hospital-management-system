import operator
from datetime import date, datetime, time
from enum import Enum

from app.core.app import App
from app.core.config import AppConfig
from app.database.models import Specialty
from app.lookups.enums import AppointmentStatusEnum
from app.pages.core.base_page import BasePage
from app.repositories.patient_profile_repository import PatientProfileLoad
from app.ui.inputs.doctor_by_specialty_input import DoctorBySpecialtyInput
from app.ui.inputs.filter_input import FilterInput, FilterItem
from app.ui.inputs.text_input import TextInput
from app.ui.menu_form import InputResult, KeyAction, MenuField, MenuForm
from app.ui.prompts import prompt_error, prompt_success
from app.validators import (
    validate_date,
    validate_date_relation,
    validate_time,
    validate_time_interval,
)
from rich.table import Table


class FieldKey(Enum):
    SPECIALTY = "Specialty"
    DOCTOR = "Doctor"
    REASON = "Reason"
    DATE = "Date"
    START_TIME = "Start Time"
    END_TIME = "End Time"
    ROOM_NAME = "Room Name"


class DoctorCreateAppointmentForPatientPage(BasePage):
    @property
    def title(self):
        return "Create appointment for patient"

    fields: list[MenuField] | None = None

    def __init__(self, app: App, patient_profile_id: int):
        super().__init__(app)
        self.patient_profile_id = patient_profile_id

    def run(self) -> BasePage | None:
        with self.app.session_scope() as session:
            patient_profile = self.app.repos.patient_profile.get(
                session,
                self.patient_profile_id,
                loaders=[*PatientProfileLoad.APPOINTMENT_REQUESTS_FULL],
            )
            if patient_profile is None:
                raise ValueError(
                    f"Patient profile id {self.patient_profile_id} does not exist."
                )
            self.appointment_request = patient_profile

        if self.fields is None:
            self.fields = self._init_fields()
        menu_form = MenuForm(self.fields, "Create appointment", submit_label="Submit")

        while True:
            self.clear()
            self.display_logged_in_header(self.app)
            # TODO

            selected_date_result: InputResult = menu_form._find_field(
                FieldKey.DATE.value
            ).input_result
            selected_date_result_date = selected_date_result.value
            selected_date_error = selected_date_result.error is not None

            if selected_date_result_date is not None and not selected_date_error:
                with self.app.session_scope() as session:
                    start_dt_search = datetime.combine(
                        selected_date_result_date, time.min
                    )
                    end_dt_search = datetime.combine(
                        selected_date_result_date, time.max
                    )
                    details = self.app.repos.appointment.list_appointment_details_by_patient_profile_id(
                        session,
                        self.patient_profile_id,
                        only_include_status_ids=[AppointmentStatusEnum.SCHEDULED],
                        datetime_range=(start_dt_search, end_dt_search),
                        order_by_start_datetime_asc=True,
                    )
                    table = Table(
                        title=f"Details of scheduled appointments for selected patient on {selected_date_result_date.strftime("%Y-%m-%d")} [YYYY-MM-DD]",
                        title_justify="left",
                    )
                    table.add_column("Start")
                    table.add_column("End")
                    table.add_column("Specialty")
                    table.add_column("Room")

                    for (
                        start_datetime,
                        end_datetime,
                        specialty_id,
                        room_name,
                    ) in details:
                        start: datetime = start_datetime
                        end: datetime = end_datetime
                        table.add_row(
                            start.time().strftime("%H:%M"),
                            end.time().strftime("%H:%M"),
                            self.app.lookup_cache.get_specialty_name(specialty_id),
                            room_name,
                        )
                    self.print(table)
                    self.print("")

            data = menu_form.run()

            if data is None:
                continue
            if data is KeyAction.BACK:
                return

            # Attempt creating appointment
            try:
                with self.app.session_scope() as session:
                    assert self.app.current_person is not None

                    date = data[FieldKey.DATE.value]
                    start_datetime = datetime.combine(
                        date, data[FieldKey.START_TIME.value]
                    )
                    end_datetime = datetime.combine(date, data[FieldKey.END_TIME.value])
                    self.app.services.appointment.create_appointment(
                        session,
                        start_datetime=start_datetime,
                        end_datetime=end_datetime,
                        patient_profile_id=self.patient_profile_id,
                        doctor_profile_id=data[FieldKey.DOCTOR.value],
                        specialty_id=data[FieldKey.SPECIALTY.value],
                        room_name=data[FieldKey.ROOM_NAME.value],
                        reason=data[FieldKey.REASON.value],
                        created_by_profile_id=self.app.current_person.profile_id,
                    )
                    prompt_success(self.console, "Appointment created successfully!")
                    return

            except Exception as e:
                prompt_error(self.console, f"Failed to create appointment request: {e}")
                continue

    def _init_fields(self) -> list[MenuField]:
        request = self.appointment_request

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
                FieldKey.DOCTOR.value,
                f"{FieldKey.DOCTOR.value} (By {FieldKey.SPECIALTY.value})",
                DoctorBySpecialtyInput(self.app),
                consumes_key=FieldKey.SPECIALTY.value,
            ),
            MenuField(
                FieldKey.REASON.value,
                FieldKey.REASON.value,
                TextInput(self.app, FieldKey.REASON.value),
            ),
            MenuField(
                FieldKey.DATE.value,
                FieldKey.DATE.value,
                TextInput(
                    self.app,
                    f"{FieldKey.DATE.value} [YYYY-MM-DD] (<{AppConfig.appointment_preferred_datetime_max_days_from_current} days from today)",
                    validators=[
                        validate_date,
                        lambda x: validate_date_relation(
                            x,
                            date.today(),
                            op=operator.gt,
                        ),
                    ],
                ),
            ),
            MenuField(
                FieldKey.START_TIME.value,
                FieldKey.START_TIME.value,
                TextInput(
                    self.app,
                    f"{FieldKey.START_TIME.value} [HH:MM], 24HR ({AppConfig.appointment_timeslot_min_interval_minutes}-minute intervals)",
                    validators=[
                        validate_time,
                        lambda x: validate_time_interval(
                            x, AppConfig.appointment_timeslot_min_interval_minutes
                        ),
                    ],
                ),
            ),
            MenuField(
                FieldKey.END_TIME.value,
                FieldKey.END_TIME.value,
                TextInput(
                    self.app,
                    f"{FieldKey.END_TIME.value} [HH:MM], 24HR ({AppConfig.appointment_timeslot_min_interval_minutes}-minute intervals)",
                    validators=[
                        validate_time,
                        lambda x: validate_time_interval(
                            x, AppConfig.appointment_timeslot_min_interval_minutes
                        ),
                    ],
                ),
            ),
            MenuField(
                FieldKey.ROOM_NAME.value,
                FieldKey.ROOM_NAME.value,
                TextInput(
                    self.app,
                    f"{FieldKey.ROOM_NAME.value} [A.01.001]",
                ),
            ),
        ]
