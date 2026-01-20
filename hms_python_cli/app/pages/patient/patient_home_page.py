from enum import Enum

from app.pages.base_page import BasePage
from app.ui.utils import prompt_choice


class PageChoice(Enum):
    VIEW_ALL_APPOINTMENTS = "View all appointments"
    CREATE_APPOINTMENT_REQUEST = "Create appointment request"
    EDIT_PERSONAL_INFORMATION = "Edit personal information"
    LOGOUT = "Logout"


class PatientHomePage(BasePage):
    selected_choice: PageChoice | None = None

    def run(self) -> BasePage | None:
        from app.pages.patient.patient_create_appointment_request_page import (
            PatientCreateAppointmentRequestPage,
        )
        from app.pages.core.edit_personal_information_page import (
            EditPersonalInformationPage,
        )

        self.clear()
        self.display_user_header(self.app)

        choices = [(choice, choice.value) for choice in PageChoice]
        self.selected_choice = prompt_choice(
            "Select action",
            choices,
            default=self.selected_choice if self.selected_choice else choices[0][0],
            exitable=False,
            show_frame=True,
        )

        match self.selected_choice:
            case PageChoice.VIEW_ALL_APPOINTMENTS:
                return
            case PageChoice.CREATE_APPOINTMENT_REQUEST:
                return PatientCreateAppointmentRequestPage(self.app)
            case PageChoice.EDIT_PERSONAL_INFORMATION:
                return EditPersonalInformationPage(self.app)
            case PageChoice.LOGOUT:
                self.app.logout()
                return
