from enum import Enum
import math

from rich.table import Table
from rich.text import Text

from app.pages.core.base_page import BasePage
from app.ui.utils import prompt_choice, KeyAction

from app.database.models import Appointment
from app.repositories.appointment_repository import AppointmentLoad
from app.lookups.enums import AppointmentStatusEnum


class PatientViewAllAppointmentsPage(BasePage):
    appointments: list[Appointment]

    items_per_scroll: int = 20
    scroll_offset: int = 0
    max_scroll_offset: int

    def run(self) -> BasePage | None:
        from app.pages.patient.patient_edit_appointment_page import (
            PatientEditAppointmentPage,
        )

        self.appointments = self._retrieve_appointments()
        self.max_scroll_offset = max(
            0, math.ceil(len(self.appointments) / self.items_per_scroll) - 1
        )

        while True:
            self.clear()
            self.display_user_header(self.app)
            self.console.print("")

            if len(self.appointments) == 0:
                print("No appointments.")
                input("Press ENTER to continue...")
                return

            self._display_all_appointment_requests()
            self.console.print("")

            visible, start_index = self._get_visible_window()

            choices = [
                (appt.appointment_id, f"No. {start_index + idx + 1}")
                for idx, appt in enumerate(visible)
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
                if self.scroll_offset > 0:
                    self.scroll_offset -= 1

            elif self.selected_choice == KeyAction.RIGHT:
                if self.scroll_offset < self.max_scroll_offset:
                    self.scroll_offset += 1

            else:
                chosen_id = self.selected_choice

    def _get_visible_window(self):
        start = self.scroll_offset * self.items_per_scroll
        end = start + self.items_per_scroll
        return self.appointments[start:end], start

    def _display_all_appointment_requests(self):
        visible, start_index = self._get_visible_window()

        title = f"Your Appointments ({start_index+1}-{start_index+len(visible)}/{len(self.appointments)})"
        table = Table(title=title, title_justify="left")
        table.add_column("No.")
        table.add_column("Status")
        table.add_column("Start")
        table.add_column("End")
        table.add_column("Room")
        table.add_column("Specialty")
        table.add_column("Reason")
        table.add_column("Doctor")

        for offset, appt in enumerate(visible):
            global_index = start_index + offset

            table.add_row(
                str(global_index + 1),
                AppointmentStatusEnum(appt.appointment_status_id).display,
                appt.start_datetime.strftime("%Y-%m-%d %H:%M"),
                appt.end_datetime.strftime("%Y-%m-%d %H:%M"),
                appt.room_name,
                appt.specialty.name,
                appt.reason,
                appt.doctor.full_name,
            )

        self.console.print(table)

    def _retrieve_appointments(self) -> list[Appointment]:
        with self.app.session_scope() as session:
            assert self.app.current_person is not None
            patient_profile_id = self.app.current_person.profile_id
            return list(
                self.app.repos.appointment.list_by_patient_profile_id(
                    session,
                    patient_profile_id,
                    loaders=(
                        AppointmentLoad.SPECIALTY,
                        AppointmentLoad.DOCTOR_WITH_PERSON,
                    ),
                )
            )
