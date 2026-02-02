from enum import Enum

from app.core.app import App
from app.pages.admin.admin_tables import (
    admin_display_doctor_profile_details_table,
    admin_display_user_details_table,
)
from app.pages.core.base_page import BasePage
from app.repositories.user_repository import UserLoad
from app.ui.prompts import KeyAction, prompt_choice, prompt_success
from rich.panel import Panel


class PageChoice(Enum):
    MANAGE_SPECIALTIES = "Manage specialties"
    ACTIVATE_DOCTOR_PROFILE = "Activate doctor profile"
    DEACTIVATE_DOCTOR_PROFILE = "Deactivate doctor profile"
    CREATE_DOCTOR_PROFILE = "Create doctor profile"


class AdminManageDoctorProfilePage(BasePage):
    @property
    def title(self):
        return "Manage doctor profile"

    def __init__(
        self,
        app: App,
        user_id: int,
    ):
        super().__init__(app)
        self.user_id = user_id
        self.doctor_profile = None

    def run(self) -> BasePage | None:
        from app.pages.admin.doctor_profile.admin_manage_specialties_for_doctor_page import (
            AdminManageSpecialtiesForDoctorPage,
        )

        while True:
            with self.app.session_scope() as session:
                user = self.app.repos.user.get(
                    session, self.user_id, loaders=[UserLoad.PERSON_WITH_PROFILES]
                )
                if user is None:
                    raise ValueError(f"User id {self.user_id} does not exist.")
                self.user = user
                self.doctor_profile = next(
                    (
                        x.doctor_profile
                        for x in user.person.profiles
                        if x.doctor_profile
                    ),
                    None,
                )

                self.clear()
                self.display_logged_in_header(self.app)
                admin_display_user_details_table(self.console, self.user)
                if self.doctor_profile:
                    admin_display_doctor_profile_details_table(
                        self.console, self.doctor_profile
                    )
                else:
                    self.print(Panel("No doctor profile.", padding=(1, 1)))
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

            if selected_choice == PageChoice.MANAGE_SPECIALTIES:
                assert self.doctor_profile is not None
                return AdminManageSpecialtiesForDoctorPage(
                    self.app, self.doctor_profile.profile_id
                )

            if selected_choice == PageChoice.ACTIVATE_DOCTOR_PROFILE:
                with self.app.session_scope() as session:
                    assert self.doctor_profile is not None
                    self.doctor_profile.profile.is_in_service = True
                    self.app.repos.doctor_profile.update(session, self.doctor_profile)
                prompt_success(self.console, "Successfully activated doctor profile.")

            if selected_choice == PageChoice.DEACTIVATE_DOCTOR_PROFILE:
                assert self.doctor_profile is not None
                with self.app.session_scope() as session:
                    self.doctor_profile.profile.is_in_service = False
                    self.app.repos.doctor_profile.update(session, self.doctor_profile)
                prompt_success(self.console, "Successfully deactivated doctor profile.")

            if selected_choice == PageChoice.CREATE_DOCTOR_PROFILE:
                with self.app.session_scope() as session:
                    self.doctor_profile = (
                        self.app.services.doctor.create_doctor_profile(
                            session, self.user.person_id
                        )
                    )
                prompt_success(self.console, "Successfully created doctor profile.")

    def _generate_choices(self):
        choices: list[tuple[PageChoice, str]] = []

        if self.doctor_profile:
            choices.append(
                (PageChoice.MANAGE_SPECIALTIES, PageChoice.MANAGE_SPECIALTIES.value)
            )

            if self.doctor_profile.profile.is_in_service:
                choices.append(
                    (
                        PageChoice.DEACTIVATE_DOCTOR_PROFILE,
                        PageChoice.DEACTIVATE_DOCTOR_PROFILE.value,
                    ),
                )
            else:
                choices.append(
                    (
                        PageChoice.ACTIVATE_DOCTOR_PROFILE,
                        PageChoice.ACTIVATE_DOCTOR_PROFILE.value,
                    ),
                )

        elif not self.doctor_profile:
            choices.append(
                (
                    PageChoice.CREATE_DOCTOR_PROFILE,
                    PageChoice.CREATE_DOCTOR_PROFILE.value,
                )
            )
        return choices
