from datetime import date, datetime, timedelta
from enum import Enum

from app.core.app import App
from app.core.config import AppConfig
from app.pages.core.base_page import BasePage
from app.pages.patient.patient_tables import (
    patient_display_appointment_requests_table,
    patient_display_appointments_table,
)
from app.repositories.appointment_repository import AppointmentLoad
from app.repositories.appointment_request_repository import AppointmentRequestLoad
from app.ui.inputs.text_input import TextInput
from app.ui.menu_form import InputResult, MenuField, MenuForm
from app.ui.prompts import KeyAction, prompt_choice, prompt_success
from app.validators import (
    validate_date,
    validate_date_in_range,
    validate_time,
    validate_time_interval,
)


class PageChoice(Enum):
    EDIT_PREFERRED_DATETIME = "Edit preferred datetime"
    CANCEL_APPOINTMENT_REQUEST = "Cancel appointment request (irreversible)"
    VIEW_LINKED_APPOINTMENT = "View linked appointment"
    BACK = "Back"


class PatientViewAppointmentRequestPage(BasePage):
    @property
    def title(self):
        return "View appointment request"

    def __init__(self, app: App, appointment_request_id: int):
        super().__init__(app)
        self.appointment_request_id = appointment_request_id

    def run(self) -> BasePage | None:
        from app.pages.patient.patient_view_appointment_page import (
            PatientViewAppointmentPage,
        )

        while True:
            with self.app.session_scope() as session:
                appointment_request = self.app.repos.appointment_request.get(
                    session,
                    self.appointment_request_id,
                    loaders=[
                        AppointmentRequestLoad.SPECIALTY,
                        AppointmentRequestLoad.PREFERRED_DOCTOR_WITH_PERSON,
                        AppointmentRequestLoad.HANDLED_BY_PROFILE,
                    ],
                )
                if appointment_request is None:
                    raise ValueError(
                        f"Appointment request id {self.appointment_request_id} does not exist."
                    )
                self.appointment_request = appointment_request

            self.clear()
            self.display_logged_in_header(self.app)
            patient_display_appointment_requests_table(
                self.console, self.appointment_request, title="Appointment Request"
            )
            if self.appointment_request.is_approved:
                assert self.appointment_request.appointment_id is not None
                appointment = self.app.repos.appointment.get(
                    session,
                    self.appointment_request.appointment_id,
                    loaders=[
                        AppointmentLoad.DOCTOR_WITH_PERSON,
                        AppointmentLoad.CREATED_BY_PROFILE,
                        AppointmentLoad.CANCELLED_BY_PROFILE,
                    ],
                )
                assert appointment is not None
                patient_display_appointments_table(
                    self.console, appointment, title="Linked Appointment"
                )

            choices = self._generate_choices()

            selected_choice = prompt_choice(
                "Select action",
                choices,
                exitable=True,
                clearable=False,
                scrollable=False,
                show_frame=True,
            )

            if selected_choice == KeyAction.BACK or selected_choice == PageChoice.BACK:
                return

            if selected_choice == PageChoice.EDIT_PREFERRED_DATETIME:
                request = self.appointment_request
                menu_form = MenuForm(
                    [
                        MenuField(
                            "Preferred Date",
                            "Preferred Date",
                            TextInput(
                                self.app,
                                f"Preferred Date [YYYY-MM-DD] (<{AppConfig.appointment_preferred_datetime_max_days_from_current} days from today)",
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
                            InputResult(
                                value=(
                                    request.preferred_datetime.date()
                                    if request.preferred_datetime
                                    else None
                                ),
                                display_value=(
                                    request.preferred_datetime.date().strftime(
                                        "%Y-%m-%d"
                                    )
                                    if request.preferred_datetime
                                    else None
                                ),
                            ),
                            required=False,
                        ),
                        MenuField(
                            "Preferred Time",
                            "Preferred Time (Date required)",
                            TextInput(
                                self.app,
                                f"Preferred Time [HH:MM], 24HR ({AppConfig.appointment_timeslot_min_interval_minutes}-minute intervals)",
                                validators=[
                                    validate_time,
                                    lambda x: validate_time_interval(
                                        x,
                                        AppConfig.appointment_timeslot_min_interval_minutes,
                                    ),
                                ],
                            ),
                            InputResult(
                                value=(
                                    request.preferred_datetime.time()
                                    if request.preferred_datetime
                                    else None
                                ),
                                display_value=(
                                    request.preferred_datetime.time().strftime("%H:%M")
                                    if request.preferred_datetime
                                    else None
                                ),
                            ),
                            required=False,
                        ),
                    ],
                    "Edit",
                    submit_label="Edit",
                )
                while True:
                    self.clear()
                    self.display_logged_in_header(self.app)
                    patient_display_appointment_requests_table(self.console, request)
                    data = menu_form.run()
                    if data is None:
                        continue
                    if data == KeyAction.BACK:
                        break
                    preferred_date = data["Preferred Date"]
                    preferred_time = data["Preferred Time"]
                    if preferred_date and preferred_time:
                        preferred_datetime = datetime.combine(
                            preferred_date, preferred_time
                        )
                    else:
                        break

                    with self.app.session_scope() as session:
                        assert self.app.current_person is not None
                        request = self.appointment_request
                        request.preferred_datetime = preferred_datetime
                        self.app.repos.appointment_request.update(session, request)
                        break

            if selected_choice == PageChoice.CANCEL_APPOINTMENT_REQUEST:
                with self.app.session_scope() as session:
                    self.app.services.appointment.update_appointment_request_cancelled(
                        session, self.appointment_request.appointment_request_id
                    )
                prompt_success(
                    self.console, "Appointment request successfully cancelled!"
                )

                continue

            if selected_choice == PageChoice.VIEW_LINKED_APPOINTMENT:
                assert self.appointment_request.appointment_id is not None
                return PatientViewAppointmentPage(
                    self.app, self.appointment_request.appointment_id
                )

    def _generate_choices(self):
        choices: list[tuple[PageChoice, str]] = []
        if self.appointment_request.is_pending:
            choices.extend(
                [
                    (
                        PageChoice.EDIT_PREFERRED_DATETIME,
                        PageChoice.EDIT_PREFERRED_DATETIME.value,
                    ),
                    (
                        PageChoice.CANCEL_APPOINTMENT_REQUEST,
                        PageChoice.CANCEL_APPOINTMENT_REQUEST.value,
                    ),
                ]
            )
        if self.appointment_request.is_approved:
            choices.append(
                (
                    PageChoice.VIEW_LINKED_APPOINTMENT,
                    PageChoice.VIEW_LINKED_APPOINTMENT.value,
                )
            )
        if len(choices) == 0:
            choices.append((PageChoice.BACK, PageChoice.BACK.value))
        return choices
