from enum import Enum

from app.core.app import App
from app.database.models import AppointmentRequest, Profile, ReceptionistProfile
from app.lookups.enums import AppointmentRequestStatusEnum, ProfileTypeEnum
from app.pages.admin.admin_tables import (
    admin_display_receptionist_profile_metadata_table,
    admin_display_user_details_table,
)
from app.pages.core.base_page import BasePage
from app.repositories.user_repository import UserLoad
from app.ui.prompts import KeyAction, prompt_choice, prompt_success
from rich.panel import Panel
from rich.table import Table


class PageChoice(Enum):
    ACTIVATE_RECEPTIONIST_PROFILE = "Activate receptionist profile"
    DEACTIVATE_RECEPTIONIST_PROFILE = "Deactivate receptionist profile"
    CREATE_RECEPTIONIST_PROFILE = "Create receptionist profile"


class AdminManageReceptionistProfilePage(BasePage):
    @property
    def title(self):
        return "Manage receptionist profile"

    def __init__(
        self,
        app: App,
        user_id: int,
    ):
        super().__init__(app)
        self.user_id = user_id
        self.receptionist_profile = None

    def run(self) -> BasePage | None:
        while True:
            with self.app.session_scope() as session:
                user = self.app.repos.user.get(
                    session, self.user_id, loaders=[UserLoad.PERSON_WITH_PROFILES]
                )
                if user is None:
                    raise ValueError(f"User id {self.user_id} does not exist.")
                self.user = user
                self.receptionist_profile = next(
                    (
                        x.receptionist_profile
                        for x in user.person.profiles
                        if x.receptionist_profile
                    ),
                    None,
                )

                self.clear()
                self.display_logged_in_header(self.app)
                admin_display_user_details_table(self.console, self.user)
                if self.receptionist_profile:
                    admin_display_receptionist_profile_metadata_table(
                        self.console, self.receptionist_profile
                    )

                    total_count = self.app.repos.appointment_request.count(
                        session,
                        conditions=[
                            AppointmentRequest.handled_by_profile_id
                            == self.receptionist_profile.profile_id
                        ],
                    )
                    approved_count = self.app.repos.appointment_request.count(
                        session,
                        conditions=[
                            AppointmentRequest.handled_by_profile_id
                            == self.receptionist_profile.profile_id,
                            AppointmentRequest.appointment_request_status_id
                            == AppointmentRequestStatusEnum.APPROVED.value,
                        ],
                    )
                    rejected_count = self.app.repos.appointment_request.count(
                        session,
                        conditions=[
                            AppointmentRequest.handled_by_profile_id
                            == self.receptionist_profile.profile_id,
                            AppointmentRequest.appointment_request_status_id
                            == AppointmentRequestStatusEnum.REJECTED.value,
                        ],
                    )
                    table = Table(title="Appointment Requests", title_justify="left")
                    table.add_column("Total Handled")
                    table.add_column("Approved")
                    table.add_column("Rejected")
                    table.add_row(
                        str(total_count), str(approved_count), str(rejected_count)
                    )
                    self.console.print(table)
                    self.print("")

                else:
                    self.print(Panel("No receptionist profile.", padding=(1, 1)))
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

            if selected_choice == PageChoice.ACTIVATE_RECEPTIONIST_PROFILE:
                with self.app.session_scope() as session:
                    assert self.receptionist_profile is not None
                    self.receptionist_profile.profile.is_in_service = True
                    self.app.repos.receptionist_profile.update(
                        session, self.receptionist_profile
                    )
                prompt_success(
                    self.console, "Successfully activated receptionist profile."
                )

            if selected_choice == PageChoice.DEACTIVATE_RECEPTIONIST_PROFILE:
                assert self.receptionist_profile is not None
                with self.app.session_scope() as session:
                    self.receptionist_profile.profile.is_in_service = False
                    self.app.repos.receptionist_profile.update(
                        session, self.receptionist_profile
                    )
                prompt_success(
                    self.console, "Successfully deactivated receptionist profile."
                )

            if selected_choice == PageChoice.CREATE_RECEPTIONIST_PROFILE:
                with self.app.session_scope() as session:
                    profile = Profile(
                        person_id=user.person_id,
                        profile_type_id=ProfileTypeEnum.RECEPTIONIST,
                    )
                    self.app.repos.profile.add(session, profile)

                    receptionist_profile = ReceptionistProfile(
                        profile_id=profile.profile_id,
                    )
                    self.receptionist_profile = self.app.repos.receptionist_profile.add(
                        session, receptionist_profile
                    )
                prompt_success(
                    self.console, "Successfully created receptionist profile."
                )

    def _generate_choices(self):
        choices: list[tuple[PageChoice, str]] = []

        if self.receptionist_profile:
            if self.receptionist_profile.profile.is_in_service:
                choices.append(
                    (
                        PageChoice.DEACTIVATE_RECEPTIONIST_PROFILE,
                        PageChoice.DEACTIVATE_RECEPTIONIST_PROFILE.value,
                    ),
                )
            else:
                choices.append(
                    (
                        PageChoice.ACTIVATE_RECEPTIONIST_PROFILE,
                        PageChoice.ACTIVATE_RECEPTIONIST_PROFILE.value,
                    ),
                )

        elif not self.receptionist_profile:
            choices.append(
                (
                    PageChoice.CREATE_RECEPTIONIST_PROFILE,
                    PageChoice.CREATE_RECEPTIONIST_PROFILE.value,
                )
            )
        return choices
