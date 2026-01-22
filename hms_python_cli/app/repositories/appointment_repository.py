from typing import Sequence
from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.interfaces import LoaderOption
from sqlalchemy import select

from app.database.models import Appointment, Profile, PatientProfile, DoctorProfile
from .base_repository import BaseRepository

from app.lookups.enums import AppointmentStatusEnum


class AppointmentLoad:
    SPECIALTY = joinedload(Appointment.specialty)
    DOCTOR_WITH_PERSON = (
        joinedload(Appointment.doctor)
        .joinedload(DoctorProfile.profile)
        .joinedload(Profile.person)
    )
    PATIENT_WITH_PERSON = (
        joinedload(Appointment.patient)
        .joinedload(PatientProfile.profile)
        .joinedload(Profile.person)
    )


class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self):
        super().__init__(Appointment)

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------
    def list_by_patient_profile_id(
        self,
        session: Session,
        patient_profile_id: int,
        *,
        only_scheduled: bool = False,
        datetime_range: tuple[datetime, datetime] | None = None,
        loaders: Sequence[LoaderOption] = (),
    ) -> Sequence[Appointment]:
        stmt = (
            select(Appointment)
            .where(Appointment.patient_profile_id == patient_profile_id)
            .options(*loaders)
        )

        if only_scheduled:
            stmt = stmt.where(
                Appointment.appointment_status_id == AppointmentStatusEnum.SCHEDULED
            )
        if datetime_range:
            start, end = datetime_range
            stmt = stmt.where(
                Appointment.start_datetime >= start,
                Appointment.end_datetime <= end,
            )

        return session.scalars(stmt).all()
