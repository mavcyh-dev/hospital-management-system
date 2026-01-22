from enum import Enum

from rich.table import Table
from rich.text import Text

from app.core.app import App

from app.pages.core.base_page import BasePage
from app.ui.utils import prompt_choice, KeyAction
from app.ui.inputs.text_input import TextInput, InputResult

from app.database.models import AppointmentRequest

from app.lookups.enums import AppointmentRequestStatusEnum, AppointmentStatusEnum

from app.repositories.appointment_request_repository import AppointmentRequestLoad


class PageChoice(Enum):
    EDIT_PREFERRED_DATETIME = "Edit preferred datetime"
    CANCEL_APPOINTMENT_REQUEST = "Cancel appointment request"
    VIEW_LINKED_APPOINTMENT = "View linked appointment"
    BACK = "Back"


class PatientViewAppointmentRequestPage(BasePage):
    def __init__(self, app: App, appointment_request_id: int):
        super().__init__(app)
        self.appointment_request_id = appointment_request_id

    def run(self) -> BasePage | None:
        while True:
            with self.app.session_scope() as session:
                appointment_request = self.app.repos.appointment_request.get(
                    session,
                    self.appointment_request_id,
                    loaders=[
                        AppointmentRequestLoad.SPECIALTY,
                        AppointmentRequestLoad.PREFERRED_DOCTOR_WITH_PERSON,
                    ],
                )
                if appointment_request is None:
                    raise ValueError(
                        f"Appointment request id {self.appointment_request_id} does not exist."
                    )
                self.appointment_request = appointment_request

            self.clear()
            self.display_user_header(self.app)
            self.print("")
            self._display_appointment_request()

            choices = self._generate_choices()

            selected_choice = prompt_choice(
                "Select action",
                choices,
                exitable=True,
                clearable=False,
                scrollable=False,
                show_frame=True,
            )

            match selected_choice:
                case KeyAction.BACK:
                    return
                case PageChoice.BACK:
                    return
                case PageChoice.EDIT_PREFERRED_DATETIME:
                    return
                case PageChoice.CANCEL_APPOINTMENT_REQUEST:
                    with self.app.session_scope() as session:
                        self.app.services.appointment.update_appointment_request_cancelled(
                            session, self.appointment_request.appointment_request_id
                        )
                    self.print_success("Appointment request successfully cancelled!")
                    input("Press ENTER to continue...")
                    continue
                case PageChoice.VIEW_LINKED_APPOINTMENT:
                    # to connect view appointment page here
                    continue

    def _display_appointment_request(self):

        table = Table(title="Appointment Request", title_justify="left")
        table.add_column("Status")
        table.add_column("Created")
        table.add_column("Specialty")
        table.add_column("Reason")
        table.add_column("Preferred Doctor")
        table.add_column("Preferred Datetime")
        if self.appointment_request.is_rejected:
            table.add_column("Rejection Datetime")
            table.add_column("Rejection Reason")
        if self.appointment_request.is_cancelled:
            table.add_column("Cancelled Datetime")

        request = self.appointment_request

        row = [
            request.status_enum.display,
            request.created_datetime.strftime("%Y-%m-%d"),
            request.specialty.name,
            request.reason,
            (
                request.preferred_doctor.full_name
                if request.preferred_doctor
                else Text("[empty]", style="italic dim")
            ),
            (
                request.preferred_datetime.strftime("%Y-%m-%d %H:%M")
                if request.preferred_datetime
                else Text("[empty]", style="italic dim")
            ),
        ]
        if self.appointment_request.is_rejected:
            assert self.appointment_request.handled_datetime is not None
            assert self.appointment_request.handling_notes is not None
            row.append(
                self.appointment_request.handled_datetime.strftime("%Y-%m-%d %H:%M")
            )
            row.append(self.appointment_request.handling_notes)
        if self.appointment_request.is_cancelled:
            assert self.appointment_request.handled_datetime
            row.append(
                self.appointment_request.handled_datetime.strftime("%Y-%m-%d %H:%M")
            )
        table.add_row(*row)
        self.print(table)

    def _generate_choices(self):
        choices: list[tuple[PageChoice, str]] = []
        if self.appointment_request.is_pending:
            choices.extend(
                [
                    (
                        PageChoice.EDIT_PREFERRED_DATETIME,
                        PageChoice.EDIT_PREFERRED_DATETIME.value,
                    ),
                    (
                        PageChoice.CANCEL_APPOINTMENT_REQUEST,
                        PageChoice.CANCEL_APPOINTMENT_REQUEST.value,
                    ),
                ]
            )
        if self.appointment_request.is_approved:
            choices.append(
                (
                    PageChoice.VIEW_LINKED_APPOINTMENT,
                    PageChoice.VIEW_LINKED_APPOINTMENT.value,
                )
            )
        if len(choices) == 0:
            choices.append((PageChoice.BACK, PageChoice.BACK.value))
        return choices
