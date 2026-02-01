from enum import Enum
from typing import Literal, cast

from app.core.app import App
from app.pages.admin.admin_tables import (
    admin_display_doctor_profile_details_table,
    admin_display_user_details_table,
)
from app.pages.core.base_page import BasePage
from app.repositories.doctor_profile_repository import DoctorProfileLoad
from app.ui.prompts import KeyAction, prompt_choice, prompt_success
from prompt_toolkit.formatted_text import FormattedText


class PageChoice(Enum):
    ADD_SPECIALTY = "Add specialty"


class AdminManageSpecialtiesForDoctorPage(BasePage):
    @property
    def title(self):
        return "Manage specialties for doctor"

    def __init__(self, app: App, doctor_profile_id: int):
        super().__init__(app)
        self.doctor_profile_id = doctor_profile_id

    def run(self) -> BasePage | None:
        from app.pages.admin.doctor_profile.admin_add_specialty_for_doctor_page import (
            AdminAddSpecialtyForDoctorPage,
        )

        while True:
            self.clear()
            self.display_logged_in_header(self.app)

            if self.doctor_profile_id is not None:
                with self.app.session_scope() as session:
                    doctor_profile = self.app.repos.doctor_profile.get(
                        session,
                        self.doctor_profile_id,
                        loaders=[
                            DoctorProfileLoad.PROFILE_WITH_PERSON_WITH_USER,
                            DoctorProfileLoad.SPECIALTIES,
                            DoctorProfileLoad.APPOINTMENTS,
                        ],
                    )
                    if doctor_profile is None:
                        raise ValueError(
                            f"Doctor profile id {self.doctor_profile_id} does not exist."
                        )

                    self.doctor_profile = doctor_profile
                    self.user = self.doctor_profile.profile.person.user
                    if self.user is None:
                        raise ValueError(
                            f"User for doctor profile id {self.doctor_profile_id} does not exist."
                        )

                    admin_display_user_details_table(self.console, self.user)
                    admin_display_doctor_profile_details_table(
                        self.console, self.doctor_profile
                    )

            choices = self._generate_choices()

            selected_choice = prompt_choice(
                "Add new specialty / Remove specialty",
                choices,
                exitable=True,
                clearable=False,
                scrollable=False,
                show_frame=True,
            )

            if selected_choice == KeyAction.BACK:
                return

            if selected_choice == PageChoice.ADD_SPECIALTY:
                return AdminAddSpecialtyForDoctorPage(self.app, self.doctor_profile_id)

            else:
                specialty = next(
                    (
                        s
                        for s in self.doctor_profile.specialties
                        if s.specialty_id == selected_choice
                    ),
                    None,
                )
                if specialty:
                    self.doctor_profile.specialties.remove(specialty)
                with self.app.session_scope() as session:
                    self.app.repos.doctor_profile.update(session, self.doctor_profile)
                prompt_success(self.console, "Successfully removed specialty.")
                continue

    def _generate_choices(self):
        choices: list[tuple[int | Literal[PageChoice.ADD_SPECIALTY], FormattedText]] = (
            []
        )
        choices.append(
            (
                PageChoice.ADD_SPECIALTY,
                cast(FormattedText, [("class:green", PageChoice.ADD_SPECIALTY.value)]),
            )
        )
        choices.extend(
            [
                (
                    specialty.specialty_id,
                    cast(FormattedText, [("class:red", specialty.name)]),
                )
                for idx, specialty in enumerate(self.doctor_profile.specialties)
            ]
        )

        return choices
