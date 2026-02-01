from enum import Enum
from typing import cast

from app.pages.core.base_page import BasePage
from app.pages.doctor.doctor_tables import doctor_display_appointments_table
from app.repositories.appointment_repository import AppointmentLoad
from app.ui.prompts import prompt_choice
from prompt_toolkit.formatted_text import FormattedText


class PageChoice(Enum):
    VIEW_ALL_APPOINTMENTS = "View all appointments"
    EDIT_PROFILE_INFORMATION = "Edit profile information"
    EDIT_PERSONAL_INFORMATION = "Edit personal information"
    LOGOUT = cast(FormattedText, [("class:red", "Logout")])


class DoctorHomePage(BasePage):
    @property
    def title(self):
        return "Doctor Home"

    selected_choice: PageChoice | None = None

    def run(self) -> BasePage | None:
        from app.pages.core.edit_personal_information_page import (
            EditPersonalInformationPage,
        )
        from app.pages.doctor.doctor_edit_profile_information_page import (
            DoctorEditProfileInformationPage,
        )
        from app.pages.doctor.doctor_view_all_appointments_page import (
            DoctorViewAllAppointmentsPage,
        )

        self.clear()
        self.display_logged_in_header(self.app)
        doctor_display_appointments_table(
            self.console,
            self._retrieve_all_appointments(),
            title="Your Appointments",
            max_count=10,
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
            case PageChoice.VIEW_ALL_APPOINTMENTS:
                return DoctorViewAllAppointmentsPage(self.app)
            case PageChoice.EDIT_PROFILE_INFORMATION:
                return DoctorEditProfileInformationPage(self.app)
            case PageChoice.EDIT_PERSONAL_INFORMATION:
                return EditPersonalInformationPage(self.app)
            case PageChoice.LOGOUT:
                self.app.logout()
                return

    def _retrieve_all_appointments(self):
        with self.app.session_scope() as session:
            assert self.app.current_person is not None
            doctor_profile_id = self.app.current_person.profile_id
            appts = self.app.repos.appointment.list_by_doctor_profile_id(
                session,
                doctor_profile_id,
                order_by_created_datetime_desc=True,
                loaders=(
                    AppointmentLoad.SPECIALTY,
                    AppointmentLoad.PATIENT_WITH_PERSON,
                    AppointmentLoad.CREATED_BY_PROFILE,
                ),
            )
            return appts
