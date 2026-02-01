import math

from app.database.models import Appointment
from app.pages.core.base_page import BasePage
from app.pages.receptionist.receptionist_tables import (
    receptionist_display_appointments_table,
)
from app.repositories.appointment_repository import AppointmentLoad
from app.ui.prompts import KeyAction, prompt_choice, prompt_continue_message


class ReceptionistViewAllCreatedAppointmentsPage(BasePage):
    @property
    def title(self):
        return "View all created appointments"

    appointments: list[Appointment]

    items_per_scroll: int = 10
    scroll_offset: int = 0
    max_scroll_offset: int

    def run(self) -> BasePage | None:

        self.appointments = self._retrieve_created_appointments()
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
            receptionist_display_appointments_table(
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
                "No action",
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
                continue

    def _retrieve_created_appointments(self) -> list[Appointment]:
        with self.app.session_scope() as session:
            assert self.app.current_person is not None
            receptionist_profile_id = self.app.current_person.profile_id
            return list(
                self.app.repos.appointment.list_by_created_by_profile_id(
                    session,
                    receptionist_profile_id,
                    order_by_created_datetime_desc=True,
                    loaders=(
                        AppointmentLoad.SPECIALTY,
                        AppointmentLoad.DOCTOR_WITH_PERSON,
                        AppointmentLoad.CANCELLED_BY_PROFILE,
                    ),
                )
            )
