from datetime import datetime, timedelta
from enum import Enum

from app.core.app import App
from app.core.config import AppConfig
from app.pages.core.base_page import BasePage
from app.pages.doctor.doctor_tables import doctor_display_appointments_table
from app.repositories.appointment_repository import AppointmentLoad
from app.ui.prompts import KeyAction, prompt_choice, prompt_success, prompt_text


class PageChoice(Enum):
    EDIT_DOCTORS_NOTES = "Edit doctor's notes"
    MANAGE_PRESCRIPTION = "Manage prescription"
    MARK_AS_COMPLETED = "Mark as completed"
    MARK_AS_MISSED = "Mark as missed"
    CANCEL_APPOINTMENT = f"Cancel appointment (>{AppConfig.appointment_min_days_from_start_allow_cancel} days from start)"
    CREATE_APPOINTMENT_FOR_PATIENT = "Create appointment for patient"
    BACK = "Back"


class DoctorWorkOnAppointmentPage(BasePage):
    @property
    def title(self):
        return "Work on appointment"

    def __init__(self, app: App, appointment_id: int):
        super().__init__(app)
        self.appointment_id = appointment_id

    def run(self) -> BasePage | None:
        from app.pages.core.cancel_appointment_page import CancelAppointmentPage
        from app.pages.doctor.doctor_create_appointment_for_patient_page import (
            DoctorCreateAppointmentForPatientPage,
        )
        from app.pages.doctor.doctor_manage_prescription_page import (
            DoctorManagePrescriptionPage,
        )

        while True:
            with self.app.session_scope() as session:
                appointment = self.app.repos.appointment.get(
                    session,
                    self.appointment_id,
                    loaders=[
                        AppointmentLoad.SPECIALTY,
                        AppointmentLoad.PATIENT_WITH_PERSON,
                        AppointmentLoad.CREATED_BY_PROFILE,
                        AppointmentLoad.PRESCRIPTION_WITH_ITEMS_WITH_MEDICATION,
                    ],
                )
                if appointment is None:
                    raise ValueError(
                        f"Appointment id {self.appointment_id} does not exist."
                    )
                self.appointment = appointment

            self.clear()
            self.display_logged_in_header(self.app)
            doctor_display_appointments_table(
                self.console, self.appointment, title="Appointment"
            )

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

            if selected_choice == PageChoice.EDIT_DOCTORS_NOTES:
                result = prompt_text(
                    PageChoice.EDIT_DOCTORS_NOTES.value,
                    default=appointment.doctor_notes,
                    exitable=True,
                    clearable=True,
                )
                if result == KeyAction.BACK:
                    continue
                if result == KeyAction.CLEAR:
                    appointment.doctor_notes = None
                else:
                    result = result.strip()
                    if len(result) == 0:
                        result = None
                    appointment.doctor_notes = result
                with self.app.session_scope() as session:
                    self.app.repos.appointment.update(session, appointment)
                    prompt_success(self.console, "Successfully edited doctor's notes.")
                    continue

            if selected_choice == PageChoice.MANAGE_PRESCRIPTION:
                if not self.appointment.prescriptions:
                    return DoctorManagePrescriptionPage(
                        self.app, appointment_id=self.appointment_id
                    )
                else:
                    # Take first prescription. There is only supposed to be a single prescription for a single appointment as of now.
                    return DoctorManagePrescriptionPage(
                        self.app,
                        prescription_id=self.appointment.prescriptions[
                            0
                        ].prescription_id,
                    )

            if selected_choice == PageChoice.MARK_AS_COMPLETED:
                with self.app.session_scope() as session:
                    self.app.services.appointment.update_appointment_completed(
                        session, self.appointment_id
                    )
                    prompt_success(self.console, "Successfully marked as completed.")

            if selected_choice == PageChoice.MARK_AS_MISSED:
                with self.app.session_scope() as session:
                    self.app.services.appointment.update_appointment_missed(
                        session, self.appointment_id
                    )
                    prompt_success(
                        self.console,
                        "Successfully marked as missed. All related prescriptions removed.",
                    )

            if selected_choice == PageChoice.CANCEL_APPOINTMENT:
                return CancelAppointmentPage(self.app, self.appointment_id)

            if selected_choice == PageChoice.CREATE_APPOINTMENT_FOR_PATIENT:
                return DoctorCreateAppointmentForPatientPage(
                    self.app, self.appointment.patient_profile_id
                )

    def _generate_choices(self):
        choices: list[tuple[PageChoice, str]] = []
        if not self.appointment.is_missed:
            choices.extend(
                [
                    (
                        PageChoice.EDIT_DOCTORS_NOTES,
                        PageChoice.EDIT_DOCTORS_NOTES.value,
                    ),
                    (
                        PageChoice.MANAGE_PRESCRIPTION,
                        PageChoice.MANAGE_PRESCRIPTION.value,
                    ),
                ]
            )

        if self.appointment.is_scheduled:
            choices.extend(
                [
                    (
                        PageChoice.MARK_AS_COMPLETED,
                        PageChoice.MARK_AS_COMPLETED.value,
                    ),
                    (
                        PageChoice.MARK_AS_MISSED,
                        PageChoice.MARK_AS_MISSED.value,
                    ),
                ]
            )
            if self.appointment.start_datetime >= (
                datetime.now()
                + timedelta(days=AppConfig.appointment_min_days_from_start_allow_cancel)
            ):
                choices.append(
                    (
                        PageChoice.CANCEL_APPOINTMENT,
                        PageChoice.CANCEL_APPOINTMENT.value,
                    )
                )

        choices.append(
            (
                PageChoice.CREATE_APPOINTMENT_FOR_PATIENT,
                PageChoice.CREATE_APPOINTMENT_FOR_PATIENT.value,
            )
        )

        if len(choices) == 0:
            choices.append((PageChoice.BACK, PageChoice.BACK.value))
        return choices
