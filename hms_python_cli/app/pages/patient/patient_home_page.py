from enum import Enum

from rich.table import Table
from rich.text import Text

from app.pages.core.base_page import BasePage
from app.ui.utils import prompt_choice

from app.lookups.enums import AppointmentRequestStatusEnum, AppointmentStatusEnum

from app.repositories.appointment_request_repository import AppointmentRequestLoad
from app.repositories.appointment_repository import AppointmentLoad


class PageChoice(Enum):
    CREATE_APPOINTMENT_REQUEST = "Create appointment request"
    VIEW_ALL_APPOINTMENT_REQUESTS = "View all appointment requests"
    VIEW_ALL_APPOINTMENTS = "View all appointments"
    EDIT_PERSONAL_INFORMATION = "Edit personal information"
    LOGOUT = "Logout"


class PatientHomePage(BasePage):
    selected_choice: PageChoice | None = None

    def run(self) -> BasePage | None:
        from app.pages.patient.patient_view_all_appointment_requests_page import (
            PatientViewAllAppointmentRequestsPage,
        )
        from app.pages.patient.patient_view_all_appointments_page import (
            PatientViewAllAppointmentsPage,
        )
        from app.pages.patient.patient_create_appointment_request_page import (
            PatientCreateAppointmentRequestPage,
        )
        from app.pages.core.edit_personal_information_page import (
            EditPersonalInformationPage,
        )

        self.clear()
        self.display_user_header(self.app)
        self.console.print("")

        self._display_all_appointment_requests()
        self.console.print("")
        self._display_scheduled_appointments()
        self.console.print("")

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

    def _display_all_appointment_requests(self):
        MAX_COUNT = 10
        with self.app.session_scope() as session:
            assert self.app.current_person is not None
            patient_profile_id = self.app.current_person.profile_id
            requests = self.app.repos.appointment_request.list_by_patient_profile_id(
                session,
                patient_profile_id,
                loaders=(
                    AppointmentRequestLoad.SPECIALTY,
                    AppointmentRequestLoad.PREFERRED_DOCTOR_WITH_PERSON,
                ),
            )
        title = "Your Appointment Requests"
        if len(requests) > MAX_COUNT:
            title += f" ({MAX_COUNT}/{len(requests)})"
        else:
            title += f" ({len(requests)})"
        table = Table(title=title, title_justify="left")
        table.add_column("Status")
        table.add_column("Created")
        table.add_column("Specialty")
        table.add_column("Reason")
        table.add_column("Preferred Doctor")
        table.add_column("Preferred Datetime")

        for request in requests[:MAX_COUNT]:
            table.add_row(
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

    def _display_scheduled_appointments(self):
        MAX_COUNT = 10
        with self.app.session_scope() as session:
            assert self.app.current_person is not None
            patient_profile_id = self.app.current_person.profile_id
            appts = self.app.repos.appointment.list_by_patient_profile_id(
                session,
                patient_profile_id=patient_profile_id,
                only_scheduled=True,
                loaders=(AppointmentLoad.SPECIALTY, AppointmentLoad.DOCTOR_WITH_PERSON),
            )

        title = "Your Appointments"
        if len(appts) > MAX_COUNT:
            title += f" ({MAX_COUNT}/{len(appts)})"
        else:
            title += f" ({len(appts)})"
        table = Table(title=title, title_justify="left")
        table.add_column("Status")
        table.add_column("Start")
        table.add_column("End")
        table.add_column("Room")
        table.add_column("Specialty")
        table.add_column("Reason")
        table.add_column("Doctor")

        for appt in appts[:MAX_COUNT]:
            table.add_row(
                AppointmentStatusEnum(appt.appointment_status_id).display,
                appt.start_datetime.strftime("%Y-%m-%d %H:%M"),
                appt.end_datetime.strftime("%Y-%m-%d %H:%M"),
                appt.room_name,
                appt.specialty.name,
                appt.reason,
                appt.doctor.full_name,
            )

        self.console.print(table)
