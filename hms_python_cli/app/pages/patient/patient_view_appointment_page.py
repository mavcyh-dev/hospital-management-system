from datetime import datetime, timedelta
from enum import Enum

from app.core.app import App
from app.pages.core.base_page import BasePage
from app.pages.patient.patient_tables import patient_display_appointments_table
from app.repositories.appointment_repository import AppointmentLoad
from app.ui.prompts import KeyAction, prompt_choice


class PageChoice(Enum):
    CANCEL_APPOINTMENT = "Cancel appointment (>2 days from start)"
    BACK = "Back"


class PatientViewAppointmentPage(BasePage):
    def __init__(self, app: App, appointment_id: int):
        super().__init__(app)
        self.appointment_id = appointment_id

    def run(self) -> BasePage | None:
        from app.pages.core.cancel_appointment_page import CancelAppointmentPage

        while True:
            with self.app.session_scope() as session:
                appointment = self.app.repos.appointment.get(
                    session,
                    self.appointment_id,
                    loaders=[
                        AppointmentLoad.SPECIALTY,
                        AppointmentLoad.DOCTOR_WITH_PERSON,
                        AppointmentLoad.CREATED_BY_PROFILE,
                        AppointmentLoad.CANCELLED_BY_PROFILE,
                    ],
                )
                if appointment is None:
                    raise ValueError(
                        f"Appointment id {self.appointment_id} does not exist."
                    )
                self.appointment = appointment

            self.clear()
            self.display_user_header(self.app)
            patient_display_appointments_table(
                self.console, self.appointment, title="Appointment"
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

            if selected_choice == PageChoice.CANCEL_APPOINTMENT:
                return CancelAppointmentPage(self.app, self.appointment_id)

    def _generate_choices(self):
        choices: list[tuple[PageChoice, str]] = []
        if self.appointment.is_scheduled:
            if self.appointment.start_datetime >= (datetime.now() + timedelta(days=2)):
                choices.append(
                    (
                        PageChoice.CANCEL_APPOINTMENT,
                        PageChoice.CANCEL_APPOINTMENT.value,
                    )
                )
            else:
                choices.append(
                    (
                        PageChoice.BACK,
                        f"{PageChoice.BACK.value} (Cancellation must be >2 days from start)",
                    )
                )
        if len(choices) == 0:
            choices.append((PageChoice.BACK, PageChoice.BACK.value))
        return choices
