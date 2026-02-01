from datetime import datetime, timedelta
from enum import Enum
from typing import cast

from app.database.models import Appointment, AppointmentRequest
from app.pages.core.base_page import BasePage
from app.ui.prompts import prompt_choice
from prompt_toolkit.formatted_text import FormattedText
from rich.table import Table


class PageChoice(Enum):
    MANAGE_USER = "Manage user"
    MANAGE_MEDICATIONS = "Manage medications"
    MANAGE_SPECIALTIES = "Manage specialties"
    EDIT_PERSONAL_INFORMATION = "Edit personal information"
    LOGOUT = cast(FormattedText, [("class:red", "Logout")])


class AdminHomePage(BasePage):
    @property
    def title(self):
        return "Admin Home"

    selected_choice: PageChoice | None = None

    def run(self) -> BasePage | None:
        from app.pages.admin.medication.admin_manage_medications_page import (
            AdminManageMedicationsPage,
        )
        from app.pages.admin.specialty.admin_manage_specialties_page import (
            AdminManageSpecialtiesPage,
        )
        from app.pages.admin.user.admin_select_user_to_manage_page import (
            AdminSelectUserToManagePage,
        )
        from app.pages.core.edit_personal_information_page import (
            EditPersonalInformationPage,
        )

        self.clear()
        self.display_logged_in_header(self.app)

        with self.app.session_scope() as session:
            patient_count = self.app.repos.patient_profile.count(session)
            doctor_count = self.app.repos.doctor_profile.count(session)
            receptionist_count = self.app.repos.receptionist_profile.count(session)
            admin_count = self.app.repos.admin_profile.count(session)
            table = Table(title="Profile Count", title_justify="left")
            table.add_column("Patient")
            table.add_column("Doctor")
            table.add_column("Receptionist")
            table.add_column("Admin")
            table.add_row(
                str(patient_count),
                str(doctor_count),
                str(receptionist_count),
                str(admin_count),
            )
            self.console.print(table)
            self.console.print("")

            request_repo = self.app.repos.appointment_request
            request_total_count = request_repo.count(session)
            request_last_month_count = request_repo.count(
                session,
                conditions=[
                    AppointmentRequest.created_datetime
                    >= (datetime.now() - timedelta(days=31))
                ],
            )
            request_last_week_count = request_repo.count(
                session,
                conditions=[
                    AppointmentRequest.created_datetime
                    >= (datetime.now() - timedelta(days=7))
                ],
            )
            request_today_count = request_repo.count(
                session,
                conditions=[
                    AppointmentRequest.created_datetime
                    >= (datetime.now() - timedelta(days=1))
                ],
            )

            table = Table(title="Appointment Requests", title_justify="left")
            table.add_column("Total")
            table.add_column("Last month")
            table.add_column("Last week")
            table.add_column("Today")
            table.add_row(
                str(request_total_count),
                str(request_last_month_count),
                str(request_last_week_count),
                str(request_today_count),
            )
            self.console.print(table)
            self.console.print("")

            appt_repo = self.app.repos.appointment
            appt_total_count = appt_repo.count(session)
            appt_last_month_count = appt_repo.count(
                session,
                conditions=[
                    Appointment.created_datetime
                    >= (datetime.now() - timedelta(days=31))
                ],
            )
            appt_last_week_count = appt_repo.count(
                session,
                conditions=[
                    Appointment.created_datetime >= (datetime.now() - timedelta(days=7))
                ],
            )
            appt_today_count = appt_repo.count(
                session,
                conditions=[
                    Appointment.created_datetime >= (datetime.now() - timedelta(days=1))
                ],
            )

            table = Table(title="Appointments", title_justify="left")
            table.add_column("Total")
            table.add_column("Last month")
            table.add_column("Last week")
            table.add_column("Today")
            table.add_row(
                str(appt_total_count),
                str(appt_last_month_count),
                str(appt_last_week_count),
                str(appt_today_count),
            )
            self.console.print(table)
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
            case PageChoice.MANAGE_USER:
                return AdminSelectUserToManagePage(self.app)
            case PageChoice.MANAGE_MEDICATIONS:
                return AdminManageMedicationsPage(self.app)
            case PageChoice.MANAGE_SPECIALTIES:
                return AdminManageSpecialtiesPage(self.app)
            case PageChoice.EDIT_PERSONAL_INFORMATION:
                return EditPersonalInformationPage(self.app)
            case PageChoice.LOGOUT:
                self.app.logout()
                return
