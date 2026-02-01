from enum import StrEnum
from typing import TYPE_CHECKING

from app.core.app import CurrentPersonDTO, CurrentUserDTO
from app.database.models import Profile
from app.lookups.enums import ProfileTypeEnum, SexEnum
from app.pages.core.base_page import BasePage
from app.ui.inputs.text_input import TextInput
from app.ui.menu_form import KeyAction, MenuField, MenuForm
from app.ui.prompts import prompt_error
from app.ui.utils import app_logo
from app.validators import validate_profile_exists_for_username

if TYPE_CHECKING:
    from app.core.app import App


class FieldKey(StrEnum):
    USERNAME = "Username"
    PASSWORD = "Password"


class LoginPage(BasePage):
    @property
    def title(self):
        return "Login"

    fields: list[MenuField] | None = None
    profile_type: ProfileTypeEnum

    def __init__(self, app: App, profile_type: ProfileTypeEnum):
        super().__init__(app)
        self.profile_type = profile_type

    def run(self) -> BasePage | None:
        from app.pages.admin.admin_home_page import AdminHomePage
        from app.pages.doctor.doctor_home_page import DoctorHomePage
        from app.pages.patient.patient_home_page import PatientHomePage
        from app.pages.receptionist.receptionist_home_page import ReceptionistHomePage

        if self.fields is None:
            self.fields = self._init_fields()
        menu_form = MenuForm(
            self.fields,
            title=f"Login as {self.profile_type.display}",
            submit_label="Login",
        )

        while True:
            self.clear()
            self.print(app_logo)
            data = menu_form.run()

            if data is None:
                continue
            if data is KeyAction.BACK:
                if len(self.app._page_stack) > 1:
                    return
                else:
                    continue

            # Attempt user login
            try:
                with self.app.session_scope() as session:
                    username = data[FieldKey.USERNAME.value]
                    user = self.app.repos.user.get_by_username(session, username)
                    if not user:
                        raise ValueError(f"Username {username} does not exist!")

                    if not self.app.services.user.validate_password(
                        session, user.user_id, data[FieldKey.PASSWORD.value]
                    ):
                        prompt_error(self.console, "Incorrect password!")
                        continue

                    person = user.person
                    profile = self.app.repos.profile.get_first(
                        session,
                        conditions=[
                            Profile.person_id == person.person_id,
                            Profile.profile_type_id == self.profile_type.value,
                        ],
                    )
                    if not profile:
                        raise ValueError(
                            f"{self.profile_type} profile does not exist for username {username}!"
                        )
                    self.app.login(
                        current_user=CurrentUserDTO(
                            user.user_id,
                            username=user.username,
                            created_datetime=user.created_datetime,
                        ),
                        current_person=CurrentPersonDTO(
                            person_id=person.person_id,
                            sex=SexEnum(person.sex),
                            first_name=person.first_name,
                            last_name=person.last_name,
                            date_of_birth=person.date_of_birth,
                            primary_email=person.primary_email,
                            primary_phone_number=person.primary_phone_number,
                            primary_home_address=person.primary_home_address,
                            profile_id=profile.profile_id,
                        ),
                        current_profile_type=self.profile_type,
                    )

                match self.profile_type:
                    case ProfileTypeEnum.PATIENT:
                        return PatientHomePage(self.app)
                    case ProfileTypeEnum.DOCTOR:
                        return DoctorHomePage(self.app)
                    case ProfileTypeEnum.RECEPTIONIST:
                        return ReceptionistHomePage(self.app)
                    case ProfileTypeEnum.ADMIN:
                        return AdminHomePage(self.app)

            except Exception as e:
                prompt_error(self.console, f"Failed to login: {e}")
                continue

    def _init_fields(self) -> list[MenuField]:
        return [
            MenuField(
                FieldKey.USERNAME.value,
                FieldKey.USERNAME.value,
                TextInput(
                    self.app,
                    FieldKey.USERNAME.value,
                    validators=lambda s: validate_profile_exists_for_username(
                        s,
                        self.app.session_scope,
                        self.app.services.user,
                        self.profile_type,
                        user_is_in_service=True,
                        profile_is_in_service=True,
                    ),
                ),
            ),
            MenuField(
                FieldKey.PASSWORD.value,
                FieldKey.PASSWORD.value,
                TextInput(self.app, FieldKey.PASSWORD.value, is_password=True),
            ),
        ]
