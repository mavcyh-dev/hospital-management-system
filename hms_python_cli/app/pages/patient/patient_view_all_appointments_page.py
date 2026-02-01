import math

from app.database.models import Appointment
from app.pages.core.base_page import BasePage
from app.pages.patient.patient_tables import patient_display_appointments_table
from app.repositories.appointment_repository import AppointmentLoad
from app.ui.prompts import KeyAction, prompt_choice, prompt_continue_message


class PatientViewAllAppointmentsPage(BasePage):
    @property
    def title(self):
        return "View all appointments"

    appointments: list[Appointment]

    items_per_scroll: int = 10
    scroll_offset: int = 0
    max_scroll_offset: int

    def run(self) -> BasePage | None:
        from app.pages.patient.patient_view_appointment_page import (
            PatientViewAppointmentPage,
        )

        self.appointments = self._retrieve_appointments()
        self.max_scroll_offset = max(
            0, math.ceil(len(self.appointments) / self.items_per_scroll) - 1
        )

        while True:
            self.clear()
            self.display_logged_in_header(self.app)

            if len(self.appointments) == 0:
                prompt_continue_message(self.console, "No appointments.")
                return

            start_index = self.scroll_offset * self.items_per_scroll
            patient_display_appointments_table(
                self.console,
                self.appointments,
                max_count=self.items_per_scroll,
                start_index=start_index,
            )

            choices = [
                (appt.appointment_id, f"No. {start_index + idx + 1}")
                for idx, appt in enumerate(
                    self.appointments[start_index : start_index + self.items_per_scroll]
                )
            ]

            self.selected_choice = prompt_choice(
                "Edit appointments",
                choices,
                exitable=True,
                clearable=False,
                scrollable=len(self.appointments) > self.items_per_scroll,
                show_frame=True,
            )

            if self.selected_choice == KeyAction.BACK:
                return
            elif self.selected_choice == KeyAction.LEFT:
                self.scroll_offset = (self.scroll_offset - 1) % (
                    self.max_scroll_offset + 1
                )
            elif self.selected_choice == KeyAction.RIGHT:
                self.scroll_offset = (self.scroll_offset + 1) % (
                    self.max_scroll_offset + 1
                )
            else:
                chosen_id = self.selected_choice
                return PatientViewAppointmentPage(self.app, chosen_id)

    def _retrieve_appointments(self) -> list[Appointment]:
        with self.app.session_scope() as session:
            assert self.app.current_person is not None
            patient_profile_id = self.app.current_person.profile_id
            return list(
                self.app.repos.appointment.list_by_patient_profile_id(
                    session,
                    patient_profile_id,
                    order_by_created_datetime_desc=True,
                    loaders=(
                        AppointmentLoad.SPECIALTY,
                        AppointmentLoad.DOCTOR_WITH_PERSON,
                        AppointmentLoad.CREATED_BY_PROFILE,
                    ),
                )
            )
