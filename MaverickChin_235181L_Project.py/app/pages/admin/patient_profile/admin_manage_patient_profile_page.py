from enum import Enum

from app.core.app import App
from app.pages.admin.admin_tables import (
    admin_display_patient_profile_details_table,
    admin_display_user_details_table,
)
from app.pages.core.base_page import BasePage
from app.repositories.user_repository import UserLoad
from app.ui.prompts import KeyAction, prompt_choice, prompt_success
from rich.panel import Panel


class PageChoice(Enum):
    ACTIVATE_PATIENT_PROFILE = "Activate patient profile"
    DEACTIVATE_PATIENT_PROFILE = "Deactivate patient profile"
    CREATE_PATIENT_PROFILE = "Create patient profile"


class AdminManagePatientProfilePage(BasePage):
    @property
    def title(self):
        return "Manage patient profile"

    def __init__(
        self,
        app: App,
        user_id: int,
    ):
        super().__init__(app)
        self.user_id = user_id
        self.patient_profile = None

    def run(self) -> BasePage | None:
        while True:
            with self.app.session_scope() as session:
                user = self.app.repos.user.get(
                    session, self.user_id, loaders=[UserLoad.PERSON_WITH_PROFILES]
                )
                if user is None:
                    raise ValueError(f"User id {self.user_id} does not exist.")
                self.user = user
                self.patient_profile = next(
                    (
                        x.patient_profile
                        for x in user.person.profiles
                        if x.patient_profile
                    ),
                    None,
                )

                self.clear()
                self.display_logged_in_header(self.app)
                admin_display_user_details_table(self.console, self.user)
                if self.patient_profile:
                    admin_display_patient_profile_details_table(
                        self.console, self.patient_profile
                    )
                else:
                    self.print(Panel("No patient profile.", padding=(1, 1)))
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

            if selected_choice == PageChoice.ACTIVATE_PATIENT_PROFILE:
                with self.app.session_scope() as session:
                    assert self.patient_profile is not None
                    self.patient_profile.profile.is_in_service = True
                    self.app.repos.patient_profile.update(session, self.patient_profile)
                prompt_success(self.console, "Successfully activated patient profile.")

            if selected_choice == PageChoice.DEACTIVATE_PATIENT_PROFILE:
                assert self.patient_profile is not None
                with self.app.session_scope() as session:
                    self.patient_profile.profile.is_in_service = False
                    self.app.repos.patient_profile.update(session, self.patient_profile)
                prompt_success(
                    self.console, "Successfully deactivated patient profile."
                )

            if selected_choice == PageChoice.CREATE_PATIENT_PROFILE:
                with self.app.session_scope() as session:
                    self.patient_profile = (
                        self.app.services.patient.create_patient_profile(
                            session, self.user.person_id
                        )
                    )
                prompt_success(self.console, "Successfully created patient profile.")

    def _generate_choices(self):
        choices: list[tuple[PageChoice, str]] = []

        if self.patient_profile:
            if self.patient_profile.profile.is_in_service:
                choices.append(
                    (
                        PageChoice.DEACTIVATE_PATIENT_PROFILE,
                        PageChoice.DEACTIVATE_PATIENT_PROFILE.value,
                    ),
                )
            else:
                choices.append(
                    (
                        PageChoice.ACTIVATE_PATIENT_PROFILE,
                        PageChoice.ACTIVATE_PATIENT_PROFILE.value,
                    ),
                )

        elif not self.patient_profile:
            choices.append(
                (
                    PageChoice.CREATE_PATIENT_PROFILE,
                    PageChoice.CREATE_PATIENT_PROFILE.value,
                )
            )
        return choices
