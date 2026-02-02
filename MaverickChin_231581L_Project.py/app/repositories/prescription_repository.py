from app.database.models import Appointment, Prescription, PrescriptionItem
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from .base_repository import BaseRepository


class PrescriptionLoad:
    PRESCRIPTION_ITEMS = selectinload(Prescription.items)
    APPOINTMENT = joinedload(Prescription.appointment)


class PrescriptionRepository(BaseRepository[Prescription]):
    def __init__(self):
        super().__init__(Prescription)

    # -------------------------------------------------------------------------
    # CREATE
    # -------------------------------------------------------------------------
    def add_prescription_for_appointment_id(
        self, session: Session, appointment_id: int
    ) -> Prescription:
        appointment = session.get(Appointment, appointment_id)
        if not appointment:
            raise ValueError(f"Appointment id {appointment_id} does not exist.")
        prescription = self.add(
            session,
            Prescription(
                patient_profile_id=appointment.patient_profile_id,
                doctor_profile_id=appointment.doctor_profile_id,
                appointment_id=appointment.appointment_id,
            ),
        )
        return prescription

    def add_prescription_item(
        self,
        session: Session,
        prescription_id: int,
        medication_id: int,
        instructions: str | None,
    ) -> PrescriptionItem:
        prescription_item = PrescriptionItem(
            prescription_id=prescription_id,
            medication_id=medication_id,
            instructions=instructions,
        )
        session.add(prescription_item)
        session.flush()
        session.refresh(prescription_item)
        return prescription_item

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------
    def get_prescription_item(
        self, session: Session, prescription_item_id: int
    ) -> PrescriptionItem | None:
        stmt = (
            select(PrescriptionItem)
            .where(PrescriptionItem.prescription_item_id == prescription_item_id)
            .options(joinedload(PrescriptionItem.medication))
        )
        return session.scalar(stmt)

    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------
    def update_prescription_item(
        self, session: Session, prescription_item: PrescriptionItem
    ):
        merged = session.merge(prescription_item)
        session.flush()
        session.refresh(merged)
        return merged

    # -------------------------------------------------------------------------
    # DELETE
    # -------------------------------------------------------------------------
    def delete_by_prescription_item_by_id_with_prescription_cleanup(
        self, session: Session, prescription_item_id: int
    ) -> None:
        prescription_item = self.get_prescription_item(session, prescription_item_id)
        if not prescription_item:
            raise ValueError(
                f"Prescription item id {prescription_item_id} does not exist."
            )
        mark_prescription_for_deletion = False
        prescription = prescription_item.prescription

        if prescription.appointment is not None:
            if len(prescription.appointment.prescriptions) <= 1:
                mark_prescription_for_deletion = False
        session.delete(prescription_item)

        if mark_prescription_for_deletion:
            session.delete(prescription)
        session.flush()
