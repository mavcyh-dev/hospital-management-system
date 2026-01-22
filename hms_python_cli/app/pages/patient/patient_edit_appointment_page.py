from enum import Enum

from rich.table import Table
from rich.text import Text

from app.pages.core.base_page import BasePage
from app.ui.utils import prompt_choice

from app.repositories.appointment_request_repository import AppointmentRequestLoad
from app.repositories.appointment_repository import AppointmentLoad


class PageChoice(Enum):
    VIEW_ALL_APPOINTMENTS = "View all appointments"
    CREATE_APPOINTMENT_REQUEST = "Create appointment request"
    EDIT_PERSONAL_INFORMATION = "Edit personal information"
    LOGOUT = "Logout"


class PatientEditAppointmentPage(BasePage):
    selected_choice: PageChoice | None = None

    def run(self) -> BasePage | None:
        pass
