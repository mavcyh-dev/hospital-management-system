from enum import Enum

from app.core.app import App
from app.pages.core.base_page import BasePage
from app.pages.patient.patient_tables import patient_display_appointments_table
from app.repositories.appointment_repository import AppointmentLoad
from app.ui.inputs.text_input import TextInput
from app.ui.menu_form import KeyAction, MenuField, MenuForm
from app.ui.prompts import prompt_success


class FieldKey(Enum):
    CANCELLATION_REASON = "Cancellation Reason"


class CancelAppointmentPage(BasePage):
    @property
    def title(self):
        return "Cancel appointment"

    fields: list[MenuField] | None = None

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

            if self.fields is None:
                self.fields = self._init_fields()

            menu_form = MenuForm(
                self.fields,
                "Cancel Appointment",
                submit_label="Cancel Appointment (Irreversible)",
            )

            while True:
                self.clear()
                self.display_logged_in_header(self.app)
                patient_display_appointments_table(self.console, self.appointment)
                data = menu_form.run()
                if data is None:
                    continue
                if data == KeyAction.BACK:
                    return
                cancellation_reason = data[FieldKey.CANCELLATION_REASON.value]

                with self.app.session_scope() as session:
                    assert self.app.current_person is not None
                    self.app.services.appointment.update_appointment_cancelled(
                        session,
                        self.appointment.appointment_id,
                        cancelled_by_profile_id=self.app.current_person.profile_id,
                        cancellation_reason=cancellation_reason,
                    )
                prompt_success(self.console, "Appointment successfully cancelled!")
                return

    def _init_fields(self) -> list[MenuField]:
        return [
            MenuField(
                FieldKey.CANCELLATION_REASON.value,
                FieldKey.CANCELLATION_REASON.value,
                TextInput(self.app, FieldKey.CANCELLATION_REASON.value),
            )
        ]
