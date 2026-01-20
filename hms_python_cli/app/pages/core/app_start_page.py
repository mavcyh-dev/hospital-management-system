from typing import TYPE_CHECKING
from enum import Enum

from app.pages.base_page import BasePage
from app.ui.utils import app_logo, prompt_choice
from app.lookups.enums import ProfileTypeEnum

if TYPE_CHECKING:
    from app.core.app import App


class PageChoice(Enum):
    PATIENT_LOGIN = ProfileTypeEnum.PATIENT
    DOCTOR_LOGIN = ProfileTypeEnum.DOCTOR
    RECEPTIONIST_LOGIN = ProfileTypeEnum.RECEPTIONIST
    ADMIN_LOGIN = ProfileTypeEnum.ADMIN
    CREATE_USER_ACCOUNT = "Create user account"
    EXIT_APPLICATION = "Exit application"


class AppStartPage(BasePage):
    profile_type: ProfileTypeEnum | None
    selected_choice: PageChoice | None = None

    def __init__(self, app: App, profile_type: ProfileTypeEnum | None = None):
        """
        :param profile_type: Skips this selection page and return login page of profile_type
        :type profile_type: Optional[ProfileTypeEnum]
        """
        super().__init__(app)
        self.profile_type = profile_type

    def run(self) -> BasePage | None:
        from app.pages.core.login_page import LoginPage
        from app.pages.core.create_user_account_page import CreateUserAccountPage

        if self.profile_type:
            return LoginPage(self.app, self.profile_type)

        self.clear()
        self.print(app_logo)

        choices = [
            (PageChoice.PATIENT_LOGIN, PageChoice.PATIENT_LOGIN.value.display),
            (PageChoice.DOCTOR_LOGIN, PageChoice.DOCTOR_LOGIN.value.display),
            (
                PageChoice.RECEPTIONIST_LOGIN,
                PageChoice.RECEPTIONIST_LOGIN.value.display,
            ),
            (PageChoice.ADMIN_LOGIN, PageChoice.ADMIN_LOGIN.value.display),
            (
                PageChoice.CREATE_USER_ACCOUNT,
                PageChoice.CREATE_USER_ACCOUNT.value,
            ),
            (
                PageChoice.EXIT_APPLICATION,
                PageChoice.EXIT_APPLICATION.value,
            ),
        ]
        self.selected_choice = prompt_choice(
            "Login as profile | Create user account",
            choices,
            default=self.selected_choice if self.selected_choice else choices[0][0],
            exitable=False,
            show_frame=True,
        )

        if self.selected_choice is None:
            return None

        match self.selected_choice:
            case PageChoice.CREATE_USER_ACCOUNT:
                return CreateUserAccountPage(self.app)
            case PageChoice.EXIT_APPLICATION:
                return
            case _:
                return LoginPage(self.app, profile_type=self.selected_choice.value)
