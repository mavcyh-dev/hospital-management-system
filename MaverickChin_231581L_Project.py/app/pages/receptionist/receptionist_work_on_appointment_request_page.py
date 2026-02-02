from enum import Enum

from app.core.app import App
from app.pages.core.base_page import BasePage
from app.pages.receptionist.receptionist_process_appointment_request import (
    ReceptionistProcessAppointmentRequestPage,
)
from app.pages.receptionist.receptionist_tables import (
    receptionist_display_appointment_requests_table,
    receptionist_display_appointments_table,
)
from app.repositories.appointment_repository import AppointmentLoad
from app.repositories.appointment_request_repository import AppointmentRequestLoad
from app.ui.inputs import TextInput
from app.ui.menu_form import MenuField, MenuForm
from app.ui.prompts import KeyAction, prompt_choice


class PageChoice(Enum):
    PROCESS_APPOINTMENT_REQUEST = "Process appointment request"
    REJECT_APPOINTMENT_REQUEST = "Reject appointment request"
    BACK = "Back"


class ReceptionistWorkOnAppointmentRequestPage(BasePage):
    @property
    def title(self):
        return "Work on appointment request"

    def __init__(self, app: App, appointment_request_id: int):
        super().__init__(app)
        self.appointment_request_id = appointment_request_id

    def run(self) -> BasePage | None:

        while True:
            with self.app.session_scope() as session:
                appointment_request = self.app.repos.appointment_request.get(
                    session,
                    self.appointment_request_id,
                    loaders=[
                        AppointmentRequestLoad.SPECIALTY,
                        AppointmentRequestLoad.PATIENT_WITH_PERSON,
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
            receptionist_display_appointment_requests_table(
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
                receptionist_display_appointments_table(
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

            if selected_choice == PageChoice.PROCESS_APPOINTMENT_REQUEST:
                return ReceptionistProcessAppointmentRequestPage(
                    self.app, self.appointment_request_id
                )

            if selected_choice == PageChoice.REJECT_APPOINTMENT_REQUEST:
                request = self.appointment_request
                menu_form = MenuForm(
                    [
                        MenuField(
                            "Rejection Reason",
                            "Rejection Reason",
                            TextInput(
                                self.app,
                                "Rejection Reason",
                            ),
                        ),
                    ],
                    "Reject appointment request",
                    submit_label="Reject",
                )
                while True:
                    self.clear()
                    self.display_logged_in_header(self.app)
                    receptionist_display_appointment_requests_table(
                        self.console, request, title="Appointment Request"
                    )
                    data = menu_form.run()
                    if data is None:
                        continue
                    if data == KeyAction.BACK:
                        break

                    handling_notes = data["Rejection Reason"]

                    with self.app.session_scope() as session:
                        assert self.app.current_person is not None
                        self.app.services.appointment.update_appointment_request_rejected(
                            session,
                            request.appointment_request_id,
                            self.app.current_person.profile_id,
                            handling_notes,
                        )
                        break

    def _generate_choices(self):
        choices: list[tuple[PageChoice, str]] = []
        if self.appointment_request.is_pending:
            choices.extend(
                [
                    (
                        PageChoice.PROCESS_APPOINTMENT_REQUEST,
                        PageChoice.PROCESS_APPOINTMENT_REQUEST.value,
                    ),
                    (
                        PageChoice.REJECT_APPOINTMENT_REQUEST,
                        PageChoice.REJECT_APPOINTMENT_REQUEST.value,
                    ),
                ]
            )
        if len(choices) == 0:
            choices.append((PageChoice.BACK, PageChoice.BACK.value))
        return choices
