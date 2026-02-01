from enum import Enum

from app.core.app import App
from app.pages.core.base_page import BasePage
from app.ui.prompts import KeyAction, prompt_choice, prompt_success
from rich.table import Table


class PageChoice(Enum):
    ACTIVATE_MEDICATION = "Activate medication"
    DEACTIVATE_MEDICATION = "Deactivate medication"


class AdminManageSelectedMedicationPage(BasePage):
    @property
    def title(self):
        return "Manage selected medication"

    def __init__(
        self,
        app: App,
        medication_id: int,
    ):
        super().__init__(app)
        self.medication_id = medication_id

    def run(self) -> BasePage | None:
        while True:
            with self.app.session_scope() as session:
                medication = self.app.repos.medication.get(
                    session,
                    self.medication_id,
                )
                if medication is None:
                    raise ValueError(
                        f"Medication id {self.medication_id} does not exist."
                    )
                self.medication = medication

            self.clear()
            self.display_logged_in_header(self.app)

            table = Table(title="Selected Medication", title_justify="left")
            table.add_column("Status")
            table.add_column("Generic Name")
            table.add_row(
                "In service" if medication.is_in_service else "Deactivated",
                medication.generic_name,
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

            if selected_choice == PageChoice.ACTIVATE_MEDICATION:
                with self.app.session_scope() as session:
                    self.medication.is_in_service = True
                    self.app.repos.medication.update(session, self.medication)
                prompt_success(self.console, "Successfully activated medication.")

            if selected_choice == PageChoice.DEACTIVATE_MEDICATION:
                with self.app.session_scope() as session:
                    self.medication.is_in_service = False
                    self.app.repos.medication.update(session, self.medication)
                prompt_success(self.console, "Successfully deactivated medication.")

    def _generate_choices(self):
        choices: list[tuple[PageChoice, str]] = []

        if self.medication:
            if self.medication.is_in_service:
                choices.append(
                    (
                        PageChoice.DEACTIVATE_MEDICATION,
                        PageChoice.DEACTIVATE_MEDICATION.value,
                    ),
                )
            else:
                choices.append(
                    (
                        PageChoice.ACTIVATE_MEDICATION,
                        PageChoice.ACTIVATE_MEDICATION.value,
                    ),
                )

        return choices
