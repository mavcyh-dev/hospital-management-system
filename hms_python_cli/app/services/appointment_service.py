from datetime import datetime

from app.database.models import Appointment, AppointmentRequest
from app.lookups.enums import AppointmentRequestStatusEnum, AppointmentStatusEnum
from app.repositories import (
    AppointmentRepository,
    AppointmentRequestRepository,
    DoctorProfileRepository,
    PatientProfileRepository,
    PersonRepository,
    PrescriptionRepository,
    UserRepository,
)
from app.services.base_service import BaseService
from sqlalchemy.orm import Session


class AppointmentService(BaseService[Appointment]):
    def __init__(
        self,
        appointment_repo: AppointmentRepository,
        appointment_request_repo: AppointmentRequestRepository,
        patient_profile_repo: PatientProfileRepository,
        doctor_profile_repo: DoctorProfileRepository,
        user_repo: UserRepository,
        person_repo: PersonRepository,
        prescription_repo: PrescriptionRepository,
    ):
        super().__init__(appointment_repo)
        self.appointment_repo = appointment_repo
        self.appointment_request_repo = appointment_request_repo
        self.patient_profile_repo = patient_profile_repo
        self.doctor_profile_repo = doctor_profile_repo
        self.user_repo = user_repo
        self.person_repo = person_repo
        self.prescription_repo = prescription_repo

    # -------------------------------------------------------------------------
    # CREATE
    # -------------------------------------------------------------------------
    def create_appointment_request(
        self,
        session: Session,
        patient_profile_id: int,
        specialty_id: int,
        reason: str,
        preferred_doctor_profile_id: int | None = None,
        preferred_datetime: datetime | None = None,
    ) -> AppointmentRequest | None:

        appointment_request = AppointmentRequest(
            patient_profile_id=patient_profile_id,
            specialty_id=specialty_id,
            reason=reason,
            preferred_doctor_profile_id=preferred_doctor_profile_id,
            preferred_datetime=preferred_datetime,
            appointment_request_status_id=AppointmentRequestStatusEnum.PENDING,
        )
        return self.appointment_request_repo.add(session, appointment_request)

    def create_appointment(
        self,
        session: Session,
        start_datetime: datetime,
        end_datetime: datetime,
        patient_profile_id: int,
        doctor_profile_id: int,
        specialty_id: int,
        room_name: str,
        reason: str,
        created_by_profile_id: int,
    ) -> Appointment | None:

        appointment = Appointment(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            patient_profile_id=patient_profile_id,
            doctor_profile_id=doctor_profile_id,
            specialty_id=specialty_id,
            room_name=room_name,
            reason=reason,
            created_by_profile_id=created_by_profile_id,
            appointment_status_id=AppointmentStatusEnum.SCHEDULED,
        )

        return self.appointment_repo.add(session, appointment)

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------

    def update_appointment_request_approved(
        self,
        session: Session,
        appointment_request_id: int,
        appointment_id: int,
        handled_by_profile_id: int,
        handling_notes: str | None,
    ) -> AppointmentRequest:
        appointment_request = self.appointment_request_repo.get(
            session, appointment_request_id
        )
        if not appointment_request:
            raise ValueError(
                f"Appointment request id {appointment_request_id} does not exist."
            )
        appointment_request.approve(
            appointment_id=appointment_id,
            handled_by_profile_id=handled_by_profile_id,
            handling_notes=handling_notes,
        )
        return self.appointment_request_repo.update(session, appointment_request)

    def update_appointment_request_cancelled(
        self,
        session: Session,
        appointment_request_id: int,
    ) -> AppointmentRequest:
        appointment_request = self.appointment_request_repo.get(
            session, appointment_request_id
        )
        if not appointment_request:
            raise ValueError(
                f"Appointment request id {appointment_request_id} does not exist."
            )
        appointment_request.cancel()
        return self.appointment_request_repo.update(session, appointment_request)

    def update_appointment_request_rejected(
        self,
        session: Session,
        appointment_request_id: int,
        handled_by_profile_id: int,
        handling_notes: str,
    ) -> AppointmentRequest:
        appointment_request = self.appointment_request_repo.get(
            session, appointment_request_id
        )
        if not appointment_request:
            raise ValueError(
                f"Appointment request id {appointment_request_id} does not exist."
            )
        appointment_request.reject(
            handled_by_profile_id=handled_by_profile_id, handling_notes=handling_notes
        )
        return self.appointment_request_repo.update(session, appointment_request)

    def update_appointment_completed(
        self, session: Session, appointment_id: int
    ) -> Appointment:
        appointment = self.appointment_repo.get(session, appointment_id)
        if not appointment:
            raise ValueError(f"Appointment id {appointment_id} does not exist.")
        appointment.complete()
        return self.appointment_repo.update(session, appointment)

    def update_appointment_cancelled(
        self,
        session: Session,
        appointment_id: int,
        cancelled_by_profile_id: int,
        cancellation_reason: str,
    ) -> Appointment:
        appointment = self.appointment_repo.get(session, appointment_id)
        if not appointment:
            raise ValueError(f"Appointment id {appointment_id} does not exist.")
        appointment.cancel(
            cancelled_by_profile_id=cancelled_by_profile_id,
            cancellation_reason=cancellation_reason,
        )
        return self.appointment_repo.update(session, appointment)

    def update_appointment_missed(
        self, session: Session, appointment_id: int
    ) -> Appointment:
        appointment = self.appointment_repo.get(session, appointment_id)
        if not appointment:
            raise ValueError(f"Appointment id {appointment_id} does not exist.")
        for prescription in appointment.prescriptions:
            session.delete(prescription)
        appointment.miss()
        return self.appointment_repo.update(session, appointment)

    # -------------------------------------------------------------------------
    # DELETE
    # -------------------------------------------------------------------------
