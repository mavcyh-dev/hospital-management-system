from enum import Enum

from app.database.models import Specialty
from app.pages.core.base_page import BasePage
from app.ui.prompts import KeyAction, prompt_choice
from rich.table import Table


class PageChoice(Enum):
    MANAGE_EXISTING_SPECIALTY = "Manage existing specialty"
    CREATE_NEW_SPECIALTY = "Create new specialty"


class AdminManageSpecialtiesPage(BasePage):
    @property
    def title(self):
        return "Manage specialties"

    selected_choice: PageChoice | None = None

    def run(self) -> BasePage | None:
        from app.pages.admin.specialty.admin_create_new_specialty_page import (
            AdminCreateNewSpecialty,
        )
        from app.pages.admin.specialty.admin_select_specialty_to_manage_page import (
            AdminSelectSpecialtyToManage,
        )

        self.clear()
        self.display_logged_in_header(self.app)

        with self.app.session_scope() as session:
            total_count = self.app.repos.specialty.count(session)
            in_service_count = self.app.repos.specialty.count(
                session, conditions=[Specialty.is_in_service.is_(True)]
            )
            deactivated_count = self.app.repos.specialty.count(
                session, conditions=[Specialty.is_in_service.is_(False)]
            )

        table = Table(title="Specialties", title_justify="left")
        table.add_column("Total")
        table.add_column("In service")
        table.add_column("Deactivated")
        table.add_row(
            str(total_count),
            str(in_service_count),
            str(deactivated_count),
        )
        self.console.print(table)
        self.console.print("")

        choices = [(choice, choice.value) for choice in PageChoice]
        selected_choice = prompt_choice(
            "Select action",
            choices,
            default=self.selected_choice if self.selected_choice else choices[0][0],
            exitable=True,
            clearable=False,
            scrollable=False,
            show_frame=True,
        )

        if selected_choice == KeyAction.BACK:
            return

        self.selected_choice = selected_choice

        match self.selected_choice:
            case PageChoice.MANAGE_EXISTING_SPECIALTY:
                return AdminSelectSpecialtyToManage(self.app)
            case PageChoice.CREATE_NEW_SPECIALTY:
                return AdminCreateNewSpecialty(self.app)
