import math

from app.core.app import App
from app.lookups.enums import AppointmentRequestStatusEnum
from app.pages.core.base_page import BasePage
from app.repositories.appointment_request_repository import AppointmentRequestLoad
from app.ui.prompts import KeyAction, prompt_choice, prompt_continue_message
from rich.table import Table
from rich.text import Text


class ReceptionistSelectFromAppointmentRequestsInSpecialty(BasePage):
    items_per_scroll: int = 10
    scroll_offset: int = 0
    max_scroll_offset: int

    def __init__(self, app: App, specialty_id: int):
        super().__init__(app)
        self.specialty_id: int = specialty_id
        self.specialty_name: str = (
            self.app.lookup_cache.get_specialty_name(self.specialty_id) or ""
        )

    def run(self) -> BasePage | None:
        from app.pages.receptionist.receptionist_work_on_appointment_request_page import (
            ReceptionistWorkOnAppointmentRequestPage,
        )

        with self.app.session_scope() as session:
            self.appointment_requests = (
                self.app.repos.appointment_request.list_by_specialty(
                    session,
                    specialty_id=self.specialty_id,
                    only_include_status_ids=[AppointmentRequestStatusEnum.PENDING],
                    order_by_created_datetime_desc=True,
                    loaders=[
                        AppointmentRequestLoad.PATIENT_WITH_PERSON,
                        AppointmentRequestLoad.PREFERRED_DOCTOR_WITH_PERSON,
                    ],
                )
            )

        self.max_scroll_offset = max(
            0, math.ceil(len(self.appointment_requests) / self.items_per_scroll) - 1
        )

        while True:
            self.clear()
            self.display_user_header(self.app)
            if len(self.appointment_requests) == 0:
                prompt_continue_message(
                    self.console,
                    f"No appointment requests for specialty {self.app.lookup_cache.get_specialty_name(self.specialty_id)}.",
                )
                return

            self._display_all_pending_appointment_requests_in_specialty()

            visible, start_index = self._get_visible_window()

            choices = [
                (
                    appointment_request.appointment_request_id,
                    f"No. {start_index + idx + 1}",
                )
                for idx, appointment_request in enumerate(visible)
            ]

            self.selected_choice = prompt_choice(
                "Select appointment request to work on",
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
                return ReceptionistWorkOnAppointmentRequestPage(self.app, choice_id)

    def _get_visible_window(self):
        start = self.scroll_offset * self.items_per_scroll
        end = start + self.items_per_scroll
        return self.appointment_requests[start:end], start

    def _display_all_pending_appointment_requests_in_specialty(self):
        visible, start_index = self._get_visible_window()

        title = f"Pending Appointment Requests for {self.specialty_name} ({start_index+1}-{start_index+len(visible)}/{len(self.appointment_requests)})"
        table = Table(title=title, title_justify="left", show_lines=True)
        table.add_column("No.")
        table.add_column("Created")
        table.add_column("Created by")
        table.add_column("Reason")
        table.add_column("Preferred Doctor")
        table.add_column("Preferred Datetime")

        for offset, request in enumerate(visible):
            global_index = start_index + offset
            table.add_row(
                str(global_index + 1),
                request.created_datetime.strftime("%Y-%m-%d"),
                request.patient.full_name,
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

        self.print(table)
        self.print("")
