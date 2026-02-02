from enum import Enum
from typing import cast

from app.pages.core.base_page import BasePage
from app.ui.prompts import prompt_choice
from prompt_toolkit.formatted_text import FormattedText
from rich.table import Table
from rich.text import Text


class PageChoice(Enum):
    SELECT_SPECIALTY_TO_WORK_ON = "Select specialty to work on"
    VIEW_ALL_CREATED_APPOINTMENTS = "View created appointments"
    EDIT_PERSONAL_INFORMATION = "Edit personal information"
    LOGOUT = cast(FormattedText, [("class:red", "Logout")])


class ReceptionistHomePage(BasePage):
    @property
    def title(self):
        return "Receptionist Home"

    selected_choice: PageChoice | None = None

    def run(self) -> BasePage | None:
        from app.pages.core.edit_personal_information_page import (
            EditPersonalInformationPage,
        )
        from app.pages.receptionist.receptionist_select_specialty_to_work_on_page import (
            ReceptionistSelectSpecialtyToWorkOnPage,
        )
        from app.pages.receptionist.receptionist_view_all_created_appointments_page import (
            ReceptionistViewAllCreatedAppointmentsPage,
        )

        self.clear()
        self.display_logged_in_header(self.app)
        self._display_all_specialties_pending_appointment_requests()

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
            case PageChoice.SELECT_SPECIALTY_TO_WORK_ON:
                return ReceptionistSelectSpecialtyToWorkOnPage(self.app)
            case PageChoice.VIEW_ALL_CREATED_APPOINTMENTS:
                return ReceptionistViewAllCreatedAppointmentsPage(self.app)
            case PageChoice.EDIT_PERSONAL_INFORMATION:
                return EditPersonalInformationPage(self.app)
            case PageChoice.LOGOUT:
                self.app.logout()
                return

    def _display_all_specialties_pending_appointment_requests(self):
        MAX_COUNT = 10
        with self.app.session_scope() as session:
            details = (
                self.app.repos.appointment_request.get_specialty_importance_details(
                    session
                )
            )
        title = f"Pending Appointment Requests by Specialty ({min(MAX_COUNT, len(details))}/{len(details)})"
        table = Table(title=title, title_justify="left")
        table.add_column("Specialty")
        table.add_column("Count")
        table.add_column("Earliest Datetime")

        for specialty_id, count, pref_dt, creation_dt in details[:MAX_COUNT]:
            name = self.app.lookup_cache.get_specialty_name(specialty_id)
            if pref_dt:
                dt = f"PREF {pref_dt.strftime("%Y-%m-%d %H:%M")}"
            else:
                dt = (
                    f"CREA {creation_dt.strftime("%Y-%m-%d %H:%M")}"
                    if creation_dt
                    else Text("[NA]", style="italic dim")
                )
            table.add_row(
                name,
                str(count),
                dt,
            )
        self.print(table)
