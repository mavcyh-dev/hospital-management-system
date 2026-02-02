from enum import Enum

from app.core.app import App
from app.pages.core.base_page import BasePage
from app.ui.prompts import KeyAction, prompt_choice, prompt_success
from rich.table import Table


class PageChoice(Enum):
    ACTIVATE_SPECIALTY = "Activate specialty"
    DEACTIVATE_SPECIALTY = "Deactivate specialty"


class AdminManageSelectedSpecialtyPage(BasePage):
    @property
    def title(self):
        return "Manage selected specialty"

    def __init__(
        self,
        app: App,
        specialty_id: int,
    ):
        super().__init__(app)
        self.specialty_id = specialty_id

    def run(self) -> BasePage | None:
        while True:
            with self.app.session_scope() as session:
                specialty = self.app.repos.specialty.get(
                    session,
                    self.specialty_id,
                )
                if specialty is None:
                    raise ValueError(
                        f"Specialty id {self.specialty_id} does not exist."
                    )
                self.specialty = specialty

            self.clear()
            self.display_logged_in_header(self.app)

            table = Table(title="Selected Specialty", title_justify="left")
            table.add_column("Status")
            table.add_column("Name")
            table.add_row(
                "In service" if specialty.is_in_service else "Deactivated",
                specialty.name,
            )
            self.print(table)
            self.print("")

            choices = self._generate_choices()

            selected_choice = prompt_choice(
                "Select action",
                choices,
                exitable=True,
                clearable=False,
                scrollable=False,
                show_frame=True,
            )

            if selected_choice == KeyAction.BACK:
                return

            if selected_choice == PageChoice.ACTIVATE_SPECIALTY:
                with self.app.session_scope() as session:
                    self.specialty.is_in_service = True
                    self.app.repos.specialty.update(session, self.specialty)
                prompt_success(self.console, "Successfully activated specialty.")

            if selected_choice == PageChoice.DEACTIVATE_SPECIALTY:
                with self.app.session_scope() as session:
                    self.specialty.is_in_service = False
                    self.app.repos.specialty.update(session, self.specialty)
                prompt_success(self.console, "Successfully deactivated specialty.")

    def _generate_choices(self):
        choices: list[tuple[PageChoice, str]] = []

        if self.specialty:
            if self.specialty.is_in_service:
                choices.append(
                    (
                        PageChoice.DEACTIVATE_SPECIALTY,
                        PageChoice.DEACTIVATE_SPECIALTY.value,
                    ),
                )
            else:
                choices.append(
                    (
                        PageChoice.ACTIVATE_SPECIALTY,
                        PageChoice.ACTIVATE_SPECIALTY.value,
                    ),
                )

        return choices
