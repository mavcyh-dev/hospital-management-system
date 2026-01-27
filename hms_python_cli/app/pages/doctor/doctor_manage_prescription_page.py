from enum import Enum
from typing import Literal

from app.core.app import App
from app.pages.core.base_page import BasePage
from app.pages.doctor.doctor_tables import (
    doctor_display_prescription_items_for_prescriptions_table,
)
from app.repositories.appointment_repository import AppointmentLoad
from app.repositories.prescription_repository import PrescriptionLoad
from app.ui.prompts import KeyAction, prompt_choice
from rich.panel import Panel


class PageChoice(Enum):
    CREATE_NEW_PRESCRIPTION_ITEM = "Create new prescription item"


class DoctorManagePrescriptionPage(BasePage):
    def __init__(
        self,
        app: App,
        *,
        prescription_id: int | None = None,
        appointment_id: int | None = None,
    ):
        super().__init__(app)
        self.prescription_id = prescription_id
        self.appointment_id = appointment_id
        self.potential_prescription_changes = False
        self.potential_prescriptions_added = None

    def run(self) -> BasePage | None:
        from app.pages.doctor.doctor_create_prescription_item_page import (
            DoctorCreatePrescriptionItemPage,
        )
        from app.pages.doctor.doctor_edit_prescription_item_page import (
            DoctorEditPrescriptionItemPage,
        )

        if (self.prescription_id is not None and self.appointment_id is not None) or (
            self.prescription_id is None and self.appointment_id is None
        ):
            raise ValueError(
                "DoctorMangePrescriptionPage should only receive either the prescription_id, or appointment_id if there is not prescription yet."
            )

        while True:
            self.clear()
            self.display_user_header(self.app)

            if self.prescription_id is not None:
                with self.app.session_scope() as session:
                    prescription = self.app.repos.prescription.get(
                        session,
                        self.prescription_id,
                        loaders=[PrescriptionLoad.PRESCRIPTION_ITEMS],
                    )
                    if prescription is None:
                        if self.potential_prescription_changes:
                            return
                        else:
                            raise ValueError(
                                f"Prescription id {self.prescription_id} does not exist."
                            )

                    self.prescription = prescription

                    doctor_display_prescription_items_for_prescriptions_table(
                        self.console, [self.prescription], show_number=True
                    )

            if self.appointment_id is not None:
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

                    if (
                        self.potential_prescription_changes
                        and appointment.prescriptions
                    ):
                        self.potential_prescriptions_added = appointment.prescriptions
                        doctor_display_prescription_items_for_prescriptions_table(
                            self.console,
                            [appointment.prescriptions[0]],
                            show_number=True,
                        )
                    else:
                        self.print(Panel("No prescription linked to appointment."))
                        self.print("")

            choices = self._generate_choices()

            selected_choice = prompt_choice(
                "Edit prescription item / Create new prescription item",
                choices,
                exitable=True,
                clearable=False,
                scrollable=False,
                show_frame=True,
            )

            if selected_choice == KeyAction.BACK:
                return

            if selected_choice == PageChoice.CREATE_NEW_PRESCRIPTION_ITEM:
                if self.prescription_id is not None:
                    return DoctorCreatePrescriptionItemPage(
                        self.app, prescription_id=self.prescription_id
                    )
                else:
                    self.potential_prescription_changes = True
                    return DoctorCreatePrescriptionItemPage(
                        self.app, appointment_id=self.appointment_id
                    )
            else:
                self.potential_prescription_changes = True
                return DoctorEditPrescriptionItemPage(self.app, selected_choice)

    def _generate_choices(self):
        choices: list[
            tuple[int | Literal[PageChoice.CREATE_NEW_PRESCRIPTION_ITEM], str]
        ] = []

        if self.prescription_id:
            choices = [
                (item.prescription_item_id, f"No. {idx + 1}")
                for idx, item in enumerate(self.prescription.items)
            ]
        if self.potential_prescriptions_added:
            choices = [
                (item.prescription_item_id, f"No. {idx + 1}")
                for idx, item in enumerate(self.potential_prescriptions_added[0].items)
            ]
        choices.append(
            (
                PageChoice.CREATE_NEW_PRESCRIPTION_ITEM,
                PageChoice.CREATE_NEW_PRESCRIPTION_ITEM.value,
            )
        )

        return choices
