from datetime import datetime, timedelta
from enum import Enum

from app.core.app import App
from app.pages.core.base_page import BasePage
from app.repositories.appointment_repository import AppointmentLoad
from app.ui.inputs.text_input import TextInput
from app.ui.menu_form import MenuField, MenuForm
from app.ui.prompts import KeyAction, prompt_choice, prompt_success
from rich.table import Table


class PageChoice(Enum):
    CANCEL_APPOINTMENT = "Cancel appointment (>24HR from start)"
    BACK = "Back"


class PatientViewAppointmentPage(BasePage):
    def __init__(self, app: App, appointment_id: int):
        super().__init__(app)
        self.appointment_id = appointment_id

    def run(self) -> BasePage | None:
        while True:
            with self.app.session_scope() as session:
                appointment = self.app.repos.appointment.get(
                    session,
                    self.appointment_id,
                    loaders=[
                        AppointmentLoad.SPECIALTY,
                        AppointmentLoad.DOCTOR_WITH_PERSON,
                        AppointmentLoad.CREATED_BY_PROFILE,
                        AppointmentLoad.CANCELLED_BY_PROFILE,
                    ],
                )
                if appointment is None:
                    raise ValueError(
                        f"Appointment id {self.appointment_id} does not exist."
                    )
                self.appointment = appointment

            self.clear()
            self.display_user_header(self.app)
            self._display_appointment()

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

            if selected_choice == PageChoice.CANCEL_APPOINTMENT:
                menu_form = MenuForm(
                    [
                        MenuField(
                            "Cancellation Reason",
                            "Cancellation Reason",
                            TextInput(
                                self.app,
                                "Cancellation Reason",
                            ),
                        )
                    ],
                    "Cancel Appointment",
                    submit_label="Cancel Appointment(Irreversible)",
                )
                while True:
                    self.clear()
                    self.display_user_header(self.app)
                    self._display_appointment()
                    data = menu_form.run()
                    if data is None:
                        continue
                    if data == KeyAction.BACK:
                        break
                    cancellation_reason = data["Cancellation Reason"]

                    with self.app.session_scope() as session:
                        assert self.app.current_person is not None
                        self.app.services.appointment.update_appointment_cancelled(
                            session,
                            self.appointment.appointment_id,
                            cancelled_by_profile_id=self.app.current_person.profile_id,
                            cancellation_reason=cancellation_reason,
                        )
                    prompt_success(
                        self.console, "\nAppointment successfully cancelled!"
                    )
                    break

    def _display_appointment(self):

        table = Table(title="Appointment", title_justify="left")
        table.add_column("Created by")
        table.add_column("Status")
        table.add_column("Start")
        table.add_column("End")
        table.add_column("Room")
        table.add_column("Specialty")
        table.add_column("Reason")
        table.add_column("Doctor")

        appt = self.appointment

        table.add_row(
            appt.created_by.type_enum.display,
            appt.status_enum.display,
            appt.start_datetime.strftime("%Y-%m-%d %H:%M"),
            appt.end_datetime.strftime("%Y-%m-%d %H:%M"),
            appt.room_name,
            appt.specialty.name,
            appt.reason,
            appt.doctor.full_name,
        )
        self.print(table)

        if self.appointment.is_cancelled:
            table = Table(title="Cancellation Details", title_justify="left")
            table.add_column("On Datetime")
            table.add_column("By")
            table.add_column("Reason")

            assert self.appointment.cancelled_by is not None
            assert self.appointment.cancelled_datetime is not None
            assert self.appointment.cancellation_reason is not None
            table.add_row(
                self.appointment.cancelled_datetime.strftime("%Y-%m-%d %H:%M"),
                self.appointment.cancelled_by.type_enum.display,
                self.appointment.cancellation_reason,
            )
            self.print(table)

    def _generate_choices(self):
        choices: list[tuple[PageChoice, str]] = []
        if self.appointment.is_scheduled and self.appointment.start_datetime >= (
            datetime.now() + timedelta(days=1)
        ):
            choices.append(
                (
                    PageChoice.CANCEL_APPOINTMENT,
                    PageChoice.CANCEL_APPOINTMENT.value,
                )
            )
        if len(choices) == 0:
            choices.append((PageChoice.BACK, PageChoice.BACK.value))
        return choices
