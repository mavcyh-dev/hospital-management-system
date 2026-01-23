import math

from app.database.models import AppointmentRequest
from app.lookups.enums import AppointmentRequestStatusEnum
from app.pages.core.base_page import BasePage
from app.repositories.appointment_request_repository import AppointmentRequestLoad
from app.ui.prompts import KeyAction, prompt_choice, prompt_continue_message
from rich.table import Table
from rich.text import Text


class PatientViewAllAppointmentRequestsPage(BasePage):
    items_per_scroll: int = 10
    scroll_offset: int = 0
    max_scroll_offset: int

    def run(self) -> BasePage | None:
        from app.pages.patient.patient_view_appointment_request_page import (
            PatientViewAppointmentRequestPage,
        )

        self.appointment_requests = self._retrieve_appointment_requests()
        self.max_scroll_offset = max(
            0, math.ceil(len(self.appointment_requests) / self.items_per_scroll) - 1
        )

        while True:
            self.clear()
            self.display_user_header(self.app)

            if len(self.appointment_requests) == 0:
                prompt_continue_message(self.console, "No appointment requests.")
                return

            self._display_all_appointment_requests()

            self.console.print("")

            visible, start_index = self._get_visible_window()

            choices = [
                (req.appointment_request_id, f"No. {start_index + idx + 1}")
                for idx, req in enumerate(visible)
            ]

            self.selected_choice = prompt_choice(
                "View appointment requests",
                choices,
                exitable=True,
                clearable=False,
                scrollable=len(self.appointment_requests) > self.items_per_scroll,
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
                choice_id = self.selected_choice
                return PatientViewAppointmentRequestPage(self.app, choice_id)

    def _get_visible_window(self):
        start = self.scroll_offset * self.items_per_scroll
        end = start + self.items_per_scroll
        return self.appointment_requests[start:end], start

    def _display_all_appointment_requests(self):
        visible, start_index = self._get_visible_window()

        title = f"Your Appointment Requests ({start_index+1}-{start_index+len(visible)}/{len(self.appointment_requests)})"
        table = Table(title=title, title_justify="left", show_lines=True)
        table.add_column("No.")
        table.add_column("Status")
        table.add_column("Created")
        table.add_column("Specialty")
        table.add_column("Reason")
        table.add_column("Preferred Doctor")
        table.add_column("Preferred Datetime")

        for offset, request in enumerate(visible):
            global_index = start_index + offset

            table.add_row(
                str(global_index + 1),
                AppointmentRequestStatusEnum(
                    request.appointment_request_status_id
                ).display,
                request.created_datetime.strftime("%Y-%m-%d"),
                request.specialty.name,
                request.reason,
                (
                    request.preferred_doctor.full_name
                    if request.preferred_doctor
                    else Text("[empty]", style="italic dim")
                ),
                (
                    request.preferred_datetime.strftime("%Y-%m-%d %H:%M")
                    if request.preferred_datetime
                    else Text("[empty]", style="italic dim")
                ),
            )

        self.console.print(table)

    def _retrieve_appointment_requests(self) -> list[AppointmentRequest]:
        with self.app.session_scope() as session:
            assert self.app.current_person is not None
            patient_profile_id = self.app.current_person.profile_id
            return list(
                self.app.repos.appointment_request.list_by_patient_profile_id(
                    session,
                    patient_profile_id,
                    order_by_created_datetime_desc=True,
                    loaders=(
                        AppointmentRequestLoad.SPECIALTY,
                        AppointmentRequestLoad.PREFERRED_DOCTOR_WITH_PERSON,
                    ),
                )
            )
