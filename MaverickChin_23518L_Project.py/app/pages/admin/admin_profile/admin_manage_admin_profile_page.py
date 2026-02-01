from enum import Enum

from app.core.app import App
from app.database.models import AdminProfile, Profile
from app.lookups.enums import ProfileTypeEnum
from app.pages.admin.admin_tables import (
    admin_display_admin_profile_metadata_table,
    admin_display_user_details_table,
)
from app.pages.core.base_page import BasePage
from app.repositories.user_repository import UserLoad
from app.ui.prompts import KeyAction, prompt_choice, prompt_success
from rich.panel import Panel


class PageChoice(Enum):
    ACTIVATE_ADMIN_PROFILE = "Activate admin profile"
    DEACTIVATE_ADMIN_PROFILE = "Deactivate admin profile"
    CREATE_ADMIN_PROFILE = "Create admin profile"


class AdminManageAdminProfilePage(BasePage):
    @property
    def title(self):
        return "Manage admin profile"

    def __init__(
        self,
        app: App,
        user_id: int,
    ):
        super().__init__(app)
        self.user_id = user_id
        self.admin_profile = None

    def run(self) -> BasePage | None:
        while True:
            with self.app.session_scope() as session:
                user = self.app.repos.user.get(
                    session, self.user_id, loaders=[UserLoad.PERSON_WITH_PROFILES]
                )
                if user is None:
                    raise ValueError(f"User id {self.user_id} does not exist.")
                self.user = user
                self.admin_profile = next(
                    (x.admin_profile for x in user.person.profiles if x.admin_profile),
                    None,
                )

                self.clear()
                self.display_logged_in_header(self.app)
                admin_display_user_details_table(self.console, self.user)
                if self.admin_profile:
                    admin_display_admin_profile_metadata_table(
                        self.console, self.admin_profile
                    )
                else:
                    self.print(Panel("No admin profile.", padding=(1, 1)))
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

            if selected_choice == PageChoice.ACTIVATE_ADMIN_PROFILE:
                with self.app.session_scope() as session:
                    assert self.admin_profile is not None
                    self.admin_profile.profile.is_in_service = True
                    self.app.repos.admin_profile.update(session, self.admin_profile)
                prompt_success(self.console, "Successfully activated admin profile.")

            if selected_choice == PageChoice.DEACTIVATE_ADMIN_PROFILE:
                assert self.admin_profile is not None
                with self.app.session_scope() as session:
                    self.admin_profile.profile.is_in_service = False
                    self.app.repos.admin_profile.update(session, self.admin_profile)
                prompt_success(self.console, "Successfully deactivated admin profile.")

            if selected_choice == PageChoice.CREATE_ADMIN_PROFILE:
                with self.app.session_scope() as session:
                    profile = Profile(
                        person_id=user.person_id,
                        profile_type_id=ProfileTypeEnum.ADMIN,
                    )
                    self.app.repos.profile.add(session, profile)

                    admin_profile = AdminProfile(
                        profile_id=profile.profile_id,
                    )
                    self.admin_profile = self.app.repos.admin_profile.add(
                        session, admin_profile
                    )
                prompt_success(self.console, "Successfully created admin profile.")

    def _generate_choices(self):
        choices: list[tuple[PageChoice, str]] = []

        if self.admin_profile:
            if self.admin_profile.profile.is_in_service:
                choices.append(
                    (
                        PageChoice.DEACTIVATE_ADMIN_PROFILE,
                        PageChoice.DEACTIVATE_ADMIN_PROFILE.value,
                    ),
                )
            else:
                choices.append(
                    (
                        PageChoice.ACTIVATE_ADMIN_PROFILE,
                        PageChoice.ACTIVATE_ADMIN_PROFILE.value,
                    ),
                )

        elif not self.admin_profile:
            choices.append(
                (
                    PageChoice.CREATE_ADMIN_PROFILE,
                    PageChoice.CREATE_ADMIN_PROFILE.value,
                )
            )
        return choices
