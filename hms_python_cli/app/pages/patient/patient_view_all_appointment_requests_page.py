import math

from app.database.models import AppointmentRequest
from app.pages.core.base_page import BasePage
from app.pages.patient.patient_tables import patient_display_appointment_requests_table
from app.repositories.appointment_request_repository import AppointmentRequestLoad
from app.ui.prompts import KeyAction, prompt_choice, prompt_continue_message


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

            start_index = self.scroll_offset * self.items_per_scroll
            patient_display_appointment_requests_table(
                self.console,
                self.appointment_requests,
                title="Your Appointment Requests",
                max_count=self.items_per_scroll,
                start_index=start_index,
            )

            choices = [
                (req.appointment_request_id, f"No. {start_index + idx + 1}")
                for idx, req in enumerate(
                    self.appointment_requests[
                        start_index : start_index + self.items_per_scroll
                    ]
                )
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

    def _retrieve_appointment_requests(self) -> list[AppointmentRequest]:
        with self.app.session_scope() as session:
            assert self.app.current_person is not None
            patient_profile_id = self.app.current_person.profile_id
            return list(
                self.app.repos.appointment_request.list_by_patient_profile_id(
                    session,
                    patient_profile_id,
                    order_by_created_datetime_desc=True,
                    loaders=[
                        AppointmentRequestLoad.SPECIALTY,
                        AppointmentRequestLoad.PREFERRED_DOCTOR_WITH_PERSON,
                    ],
                )
            )
