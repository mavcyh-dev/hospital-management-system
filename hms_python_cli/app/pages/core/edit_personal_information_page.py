from typing import Any

from enum import Enum
import time
from datetime import date
import operator
from sqlalchemy.orm import Session

from app.database.models.user_person import User
from app.core.app import CurrentUserDTO, CurrentPersonDTO

from app.ui.menu_form import MenuForm, MenuField
from app.ui.input_result import InputResult
from app.ui.inputs.text_input import TextInput
from app.ui.inputs.enum_input import EnumInput
from app.pages.core.base_page import BasePage
from app.lookups.enums import SexEnum
from app.validators import (
    validate_date,
    validate_date_relation,
    validate_email,
    validate_phone_number,
)


class FieldKey(Enum):
    FIRST_NAME = "First Name"
    LAST_NAME = "Last Name"
    SEX = "Sex"
    DATE_OF_BIRTH = "Date of Birth"
    EMAIL = "Email"
    PHONE_NUMBER = "Phone Number"
    HOME_ADDRESS = "Home Address"


class EditPersonalInformationPage(BasePage):
    fields: list[MenuField] | None = None

    def run(self) -> BasePage | None:

        self.clear()

        if self.fields is None:
            self.fields = self._init_fields()

        while True:
            menu_form = MenuForm(
                self.fields,
                title="Edit personal information",
                submit_label="Edit",
            )
            data = menu_form.run(self.console)

            if data is None:
                return None

            # Attempt to edit personal information
            try:
                with self.app.session_scope() as session:
                    self._update_person_info(session, data)
                    assert self.app.current_person is not None
                    person = self.app.services.person.get_by_id(
                        session, self.app.current_person.person_id
                    )
                    if not person:
                        raise ValueError("Current person does not exist!")

                    self.app.current_person = CurrentPersonDTO(
                        person_id=person.person_id,
                        sex=SexEnum(person.sex),
                        first_name=person.first_name,
                        last_name=person.last_name,
                        date_of_birth=person.date_of_birth,
                        primary_email=person.primary_email,
                        primary_phone_number=person.primary_phone_number,
                        primary_home_address=person.primary_home_address,
                        profile_id=self.app.current_person.profile_id,
                    )
                    self.print_success("Personal information edited successfully.")
                    time.sleep(2)
                    continue

            except Exception as e:
                self.print_error(f"Failed to create account: {e}")
                input("Press Enter to continue...")
                continue

    def _init_fields(self) -> list[MenuField]:
        user = self.app.current_user
        person = self.app.current_person
        assert user is not None
        assert person is not None
        return [
            MenuField(
                FieldKey.FIRST_NAME.value,
                FieldKey.FIRST_NAME.value,
                TextInput(self.app, FieldKey.FIRST_NAME.value),
                InputResult(value=person.first_name),
            ),
            MenuField(
                FieldKey.LAST_NAME.value,
                FieldKey.LAST_NAME.value,
                TextInput(self.app, FieldKey.LAST_NAME.value),
                InputResult(value=person.last_name),
            ),
            MenuField(
                FieldKey.SEX.value,
                FieldKey.SEX.value,
                EnumInput(
                    self.app,
                    FieldKey.SEX.value,
                    allowed=[SexEnum.MALE, SexEnum.FEMALE, SexEnum.NOT_APPLICABLE],
                ),
                InputResult(value=person.sex.value, display_value=person.sex.display),
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
                InputResult(
                    value=person.date_of_birth,
                    display_value=person.date_of_birth.strftime("%Y-%m-%d"),
                ),
            ),
            MenuField(
                FieldKey.EMAIL.value,
                FieldKey.EMAIL.value,
                TextInput(self.app, FieldKey.EMAIL.value, validators=validate_email),
                InputResult(value=person.primary_email),
            ),
            MenuField(
                FieldKey.PHONE_NUMBER.value,
                FieldKey.PHONE_NUMBER.value,
                TextInput(
                    self.app,
                    FieldKey.PHONE_NUMBER.value,
                    validators=validate_phone_number,
                ),
                InputResult(value=person.primary_phone_number),
            ),
            MenuField(
                FieldKey.HOME_ADDRESS.value,
                FieldKey.HOME_ADDRESS.value,
                TextInput(self.app, FieldKey.HOME_ADDRESS.value),
                InputResult(value=person.primary_home_address),
            ),
        ]

    def _update_person_info(self, session: Session, data: dict[str, Any]):
        assert self.app.current_person is not None
        self.app.services.person.update_person_info(
            session=session,
            person_id=self.app.current_person.person_id,
            sex=data[FieldKey.SEX.value],
            first_name=data[FieldKey.FIRST_NAME.value],
            last_name=data[FieldKey.LAST_NAME.value],
            date_of_birth=data[FieldKey.DATE_OF_BIRTH.value],
            primary_email=data[FieldKey.EMAIL.value],
            primary_phone_number=data[FieldKey.PHONE_NUMBER.value],
            primary_home_address=data[FieldKey.HOME_ADDRESS.value],
        )
