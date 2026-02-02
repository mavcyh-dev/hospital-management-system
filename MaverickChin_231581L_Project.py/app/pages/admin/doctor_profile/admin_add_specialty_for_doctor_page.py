from enum import Enum

from app.core.app import App
from app.database.models import Specialty
from app.pages.admin.admin_tables import (
    admin_display_doctor_profile_details_table,
)
from app.pages.core.base_page import BasePage
from app.repositories.doctor_profile_repository import DoctorProfileLoad
from app.ui.inputs.filter_input import FilterInput, FilterItem
from app.ui.menu_form import KeyAction, MenuField, MenuForm
from app.ui.prompts import prompt_error, prompt_success
from sqlalchemy import select


class FieldKey(Enum):
    SPECIALTY = "Specialty"


class AdminAddSpecialtyForDoctorPage(BasePage):
    @property
    def title(self):
        return "Add specialty for doctor"

    fields: list[MenuField] | None = None

    def __init__(self, app: App, doctor_profile_id: int):
        super().__init__(app)
        self.doctor_profile_id = doctor_profile_id

    def run(self) -> BasePage | None:
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

        if self.fields is None:
            self.fields = self._init_fields()
        menu_form = MenuForm(self.fields, "Select specialty", submit_label="Submit")

        while True:
            self.clear()
            self.display_logged_in_header(self.app)

            assert self.user is not None
            admin_display_doctor_profile_details_table(
                self.console, self.doctor_profile
            )

            data = menu_form.run()

            if data is None:
                continue
            if data is KeyAction.BACK:
                return

            # Attempt adding specialty
            try:
                with self.app.session_scope() as session:
                    doctor = session.merge(self.doctor_profile)

                    new_specialty = session.scalar(
                        select(Specialty).where(
                            Specialty.specialty_id == data[FieldKey.SPECIALTY.value]
                        )
                    )

                    if new_specialty is None:
                        raise ValueError(
                            f"Specialty id {data[FieldKey.SPECIALTY.value]} does not exist."
                        )

                    doctor.specialties.append(new_specialty)
                    prompt_success(self.console, "Successfully added specialty.")

            except Exception as e:
                prompt_error(self.console, f"Failed to add specialty: {e}")
                continue

    def _init_fields(self) -> list[MenuField]:
        return [
            MenuField(
                FieldKey.SPECIALTY.value,
                FieldKey.SPECIALTY.value,
                FilterInput(
                    self.app,
                    "Select specialty to add",
                    [
                        FilterItem(
                            value=s_id,
                            filter_values=[name],
                        )
                        for s_id, name in self.app.lookup_cache.get_all_specialties()
                        if s_id
                        not in {s.specialty_id for s in self.doctor_profile.specialties}
                    ],
                ),
            ),
        ]
