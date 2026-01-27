from enum import Enum
from typing import cast

from app.pages.core.base_page import BasePage
from app.pages.patient.patient_tables import (
    patient_display_appointment_requests_table,
    patient_display_appointments_table,
)
from app.repositories.appointment_repository import AppointmentLoad
from app.repositories.appointment_request_repository import AppointmentRequestLoad
from app.ui.prompts import prompt_choice
from prompt_toolkit.formatted_text import FormattedText


class PageChoice(Enum):
    CREATE_APPOINTMENT_REQUEST = "Create appointment request"
    VIEW_ALL_APPOINTMENT_REQUESTS = "View all appointment requests"
    VIEW_ALL_APPOINTMENTS = "View all appointments"
    EDIT_PERSONAL_INFORMATION = "Edit personal information"
    LOGOUT = cast(FormattedText, [("class:red", "Logout")])


class PatientHomePage(BasePage):
    selected_choice: PageChoice | None = None

    def run(self) -> BasePage | None:
        from app.pages.core.edit_personal_information_page import (
            EditPersonalInformationPage,
        )
        from app.pages.patient.patient_create_appointment_request_page import (
            PatientCreateAppointmentRequestPage,
        )
        from app.pages.patient.patient_view_all_appointment_requests_page import (
            PatientViewAllAppointmentRequestsPage,
        )
        from app.pages.patient.patient_view_all_appointments_page import (
            PatientViewAllAppointmentsPage,
        )

        self.clear()
        self.display_user_header(self.app)
        patient_display_appointment_requests_table(
            self.console,
            self._retrieve_all_appointment_requests(),
            title="Your Appointment Requests",
            max_count=5,
        )
        patient_display_appointments_table(
            self.console,
            self._retrieve_all_appointments(),
            title="Your Appointments",
            max_count=5,
        )
        self._retrieve_all_appointments()

        choices = [(choice, choice.value) for choice in PageChoice]
        self.selected_choice = prompt_choice(
            "Select action",
            choices,
            default=self.selected_choice if self.selected_choice else choices[0][0],
            exitable=False,
            clearable=False,
            scrollable=False,
            show_frame=True,
        )

        match self.selected_choice:
            case PageChoice.CREATE_APPOINTMENT_REQUEST:
                return PatientCreateAppointmentRequestPage(self.app)
            case PageChoice.VIEW_ALL_APPOINTMENT_REQUESTS:
                return PatientViewAllAppointmentRequestsPage(self.app)
            case PageChoice.VIEW_ALL_APPOINTMENTS:
                return PatientViewAllAppointmentsPage(self.app)
            case PageChoice.EDIT_PERSONAL_INFORMATION:
                return EditPersonalInformationPage(self.app)
            case PageChoice.LOGOUT:
                self.app.logout()
                return

    def _retrieve_all_appointment_requests(self):
        with self.app.session_scope() as session:
            assert self.app.current_person is not None
            patient_profile_id = self.app.current_person.profile_id
            requests = self.app.repos.appointment_request.list_by_patient_profile_id(
                session,
                patient_profile_id,
                order_by_created_datetime_desc=True,
                loaders=(
                    AppointmentRequestLoad.SPECIALTY,
                    AppointmentRequestLoad.PREFERRED_DOCTOR_WITH_PERSON,
                ),
            )
            return requests

    def _retrieve_all_appointments(self):
        with self.app.session_scope() as session:
            assert self.app.current_person is not None
            patient_profile_id = self.app.current_person.profile_id
            appts = self.app.repos.appointment.list_by_patient_profile_id(
                session,
                patient_profile_id,
                order_by_created_datetime_desc=True,
                loaders=(
                    AppointmentLoad.SPECIALTY,
                    AppointmentLoad.DOCTOR_WITH_PERSON,
                    AppointmentLoad.CREATED_BY_PROFILE,
                ),
            )
            return appts
