from enum import Enum

from app.core.app import App
from app.pages.admin.admin_tables import admin_display_user_details_table
from app.pages.core.base_page import BasePage
from app.repositories.user_repository import UserLoad
from app.ui.prompts import KeyAction, prompt_choice, prompt_success


class PageChoice(Enum):
    MANAGE_PATIENT_PROFILE = "Manage patient profile"
    MANAGE_DOCTOR_PROFILE = "Manage doctor profile"
    MANAGE_RECEPTIONIST_PROFILE = "Manage receptionist profile"
    MANAGE_ADMIN_PROFILE = "Manage admin profile"
    ACTIVATE_USER = "Activate user"
    DEACTIVATE_USER = "Deactivate user"
    BACK = "Back"


class AdminManageSelectedUserPage(BasePage):
    @property
    def title(self):
        return "Manage selected user"

    def __init__(self, app: App, user_id: int):
        super().__init__(app)
        self.user_id = user_id

    def run(self) -> BasePage | None:
        from app.pages.admin.admin_profile.admin_manage_admin_profile_page import (
            AdminManageAdminProfilePage,
        )
        from app.pages.admin.doctor_profile.admin_manage_doctor_profile_page import (
            AdminManageDoctorProfilePage,
        )
        from app.pages.admin.patient_profile.admin_manage_patient_profile_page import (
            AdminManagePatientProfilePage,
        )
        from app.pages.admin.receptionist_profile.admin_manage_receptionist_profile_page import (
            AdminManageReceptionistProfilePage,
        )

        while True:
            with self.app.session_scope() as session:
                user = self.app.repos.user.get(
                    session,
                    self.user_id,
                    loaders=[UserLoad.PERSON_WITH_PROFILES],
                )
                if user is None:
                    raise ValueError(f"User id {self.user_id} does not exist.")
                self.user = user

            self.clear()
            self.display_logged_in_header(self.app)
            admin_display_user_details_table(self.console, self.user)

            choices = self._generate_choices()

            selected_choice = prompt_choice(
                "Select action",
                choices,
                exitable=True,
                clearable=False,
                scrollable=False,
                show_frame=True,
            )

            if selected_choice == KeyAction.BACK or selected_choice == PageChoice.BACK:
                return

            if selected_choice == PageChoice.MANAGE_PATIENT_PROFILE:
                return AdminManagePatientProfilePage(self.app, self.user_id)

            if selected_choice == PageChoice.MANAGE_DOCTOR_PROFILE:
                return AdminManageDoctorProfilePage(self.app, self.user_id)

            if selected_choice == PageChoice.MANAGE_RECEPTIONIST_PROFILE:
                return AdminManageReceptionistProfilePage(self.app, self.user_id)

            if selected_choice == PageChoice.MANAGE_ADMIN_PROFILE:
                return AdminManageAdminProfilePage(self.app, self.user_id)

            if selected_choice == PageChoice.ACTIVATE_USER:
                with self.app.session_scope() as session:
                    user.is_in_service = True
                    self.app.repos.user.update(session, user)
                prompt_success(self.console, "Successfully activated user.")

            if selected_choice == PageChoice.DEACTIVATE_USER:
                with self.app.session_scope() as session:
                    user.is_in_service = False
                    self.app.repos.user.update(session, user)
                prompt_success(self.console, "Successfully deactivated user.")

    def _generate_choices(self):
        choices: list[tuple[PageChoice, str]] = []
        choices.extend(
            [
                (
                    PageChoice.MANAGE_PATIENT_PROFILE,
                    PageChoice.MANAGE_PATIENT_PROFILE.value,
                ),
                (
                    PageChoice.MANAGE_DOCTOR_PROFILE,
                    PageChoice.MANAGE_DOCTOR_PROFILE.value,
                ),
                (
                    PageChoice.MANAGE_RECEPTIONIST_PROFILE,
                    PageChoice.MANAGE_RECEPTIONIST_PROFILE.value,
                ),
                (
                    PageChoice.MANAGE_ADMIN_PROFILE,
                    PageChoice.MANAGE_ADMIN_PROFILE.value,
                ),
            ]
        )
        if self.user.is_in_service:
            choices.append(
                (
                    PageChoice.DEACTIVATE_USER,
                    PageChoice.DEACTIVATE_USER.value,
                ),
            )
        else:
            choices.append(
                (
                    PageChoice.ACTIVATE_USER,
                    PageChoice.ACTIVATE_USER.value,
                ),
            )
        return choices
