import operator
from datetime import date
from enum import Enum
from typing import Any

from app.database.models.user_person import User
from app.lookups.enums import SexEnum
from app.pages.core.base_page import BasePage
from app.ui.inputs.enum_input import EnumInput
from app.ui.inputs.text_input import TextInput
from app.ui.menu_form import KeyAction, MenuField, MenuForm
from app.ui.prompts import prompt_error, prompt_success
from app.validators import (
    validate_date,
    validate_date_relation,
    validate_email,
    validate_password,
    validate_phone_number,
)
from sqlalchemy.orm import Session


class FieldKey(Enum):
    USERNAME = "Username"
    PASSWORD = "Password"
    FIRST_NAME = "First Name"
    LAST_NAME = "Last Name"
    SEX = "Sex"
    DATE_OF_BIRTH = "Date of Birth"
    EMAIL = "Email"
    PHONE_NUMBER = "Phone Number"
    HOME_ADDRESS = "Home Address"


class CreateUserAccountPage(BasePage):
    @property
    def title(self):
        return "Create user account"

    fields: list[MenuField] | None = None

    def run(self) -> BasePage | None:
        if self.fields is None:
            self.fields = self._init_fields()
        menu_form = MenuForm(self.fields, "Create User Account", submit_label="Create")

        while True:
            self.clear()
            self.display_logged_in_header(self.app)
            data = menu_form.run()

            if data is None:
                continue
            if data is KeyAction.BACK:
                return

            # Attempt user creation
            try:
                with self.app.session_scope() as session:
                    self._create_user_with_patient_profile(session, data)
                    prompt_success(
                        self.console,
                        "User account created successfully! Patient profile automatically added.",
                    )
                    return

            except Exception as e:
                prompt_error(self.console, f"Failed to create account: {e}")
                continue

    def _init_fields(self) -> list[MenuField]:
        return [
            MenuField(
                FieldKey.USERNAME.value,
                FieldKey.USERNAME.value,
                TextInput(self.app, FieldKey.USERNAME.value),
            ),
            MenuField(
                FieldKey.PASSWORD.value,
                FieldKey.PASSWORD.value,
                TextInput(
                    self.app,
                    FieldKey.PASSWORD.value,
                    is_password=True,
                    validators=validate_password,
                ),
            ),
            MenuField(
                FieldKey.FIRST_NAME.value,
                FieldKey.FIRST_NAME.value,
                TextInput(self.app, FieldKey.FIRST_NAME.value),
            ),
            MenuField(
                FieldKey.LAST_NAME.value,
                FieldKey.LAST_NAME.value,
                TextInput(self.app, FieldKey.LAST_NAME.value),
            ),
            MenuField(
                FieldKey.SEX.value,
                FieldKey.SEX.value,
                EnumInput(
                    self.app,
                    FieldKey.SEX.value,
                    allowed=[SexEnum.MALE, SexEnum.FEMALE, SexEnum.NOT_APPLICABLE],
                ),
            ),
            MenuField(
                FieldKey.DATE_OF_BIRTH.value,
                FieldKey.DATE_OF_BIRTH.value,
                TextInput(
                    self.app,
                    f"{FieldKey.DATE_OF_BIRTH.value} [YYYY-MM-DD]",
                    validators=[
                        validate_date,
                        lambda x: validate_date_relation(x, date.today(), operator.lt),
                    ],
                ),
            ),
            MenuField(
                FieldKey.EMAIL.value,
                FieldKey.EMAIL.value,
                TextInput(self.app, FieldKey.EMAIL.value, validators=validate_email),
            ),
            MenuField(
                FieldKey.PHONE_NUMBER.value,
                FieldKey.PHONE_NUMBER.value,
                TextInput(
                    self.app,
                    FieldKey.PHONE_NUMBER.value,
                    validators=validate_phone_number,
                ),
            ),
            MenuField(
                FieldKey.HOME_ADDRESS.value,
                FieldKey.HOME_ADDRESS.value,
                TextInput(self.app, FieldKey.HOME_ADDRESS.value),
            ),
        ]

    def _create_user_with_patient_profile(
        self, session: Session, data: dict[str, Any]
    ) -> User:
        user = self.app.services.user.create_user_and_person(
            session=session,
            username=data[FieldKey.USERNAME.value],
            plain_password=data[FieldKey.PASSWORD.value],
            sex=data[FieldKey.SEX.value],
            first_name=data[FieldKey.FIRST_NAME.value],
            last_name=data[FieldKey.LAST_NAME.value],
            date_of_birth=data[FieldKey.DATE_OF_BIRTH.value],
            primary_email=data[FieldKey.EMAIL.value],
            primary_phone_number=data[FieldKey.PHONE_NUMBER.value],
            primary_home_address=data[FieldKey.HOME_ADDRESS.value],
        )
        self.app.services.patient.create_patient_profile(session, user.person_id)
        return user
