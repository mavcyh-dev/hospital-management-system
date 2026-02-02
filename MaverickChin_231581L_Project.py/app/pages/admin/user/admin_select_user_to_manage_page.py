from enum import StrEnum

from app.pages.core.base_page import BasePage
from app.ui.inputs.text_input import TextInput
from app.ui.menu_form import KeyAction, MenuField, MenuForm
from app.ui.prompts import prompt_error
from app.validators import validate_user_exists_for_username


class FieldKey(StrEnum):
    USERNAME = "Username"


class AdminSelectUserToManagePage(BasePage):
    @property
    def title(self):
        return "Select user to manage"

    fields: list[MenuField] | None = None

    def run(self) -> BasePage | None:
        from app.pages.admin.user.admin_manage_selected_user_page import (
            AdminManageSelectedUserPage,
        )

        if self.fields is None:
            self.fields = self._init_fields()
        menu_form = MenuForm(
            self.fields,
            title="Select user",
            submit_label="Select",
        )

        while True:
            self.clear()
            self.display_logged_in_header(self.app)
            data = menu_form.run()

            if data is None:
                continue
            if data is KeyAction.BACK:
                return

            # Attempt user selection
            try:
                with self.app.session_scope() as session:
                    username = data[FieldKey.USERNAME.value]
                    user = self.app.repos.user.get_by_username(session, username)
                    if not user:
                        raise ValueError(f"Username {username} does not exist!")

                return AdminManageSelectedUserPage(self.app, user.user_id)

            except Exception as e:
                prompt_error(self.console, f"Failed to select user: {e}")
                continue

    def _init_fields(self) -> list[MenuField]:
        return [
            MenuField(
                FieldKey.USERNAME.value,
                FieldKey.USERNAME.value,
                TextInput(
                    self.app,
                    FieldKey.USERNAME.value,
                    validators=lambda s: validate_user_exists_for_username(
                        s, self.app.session_scope, self.app.services.user
                    ),
                ),
            ),
        ]
