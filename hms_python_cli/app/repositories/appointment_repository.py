from datetime import datetime
from typing import Sequence

from app.database.models import Appointment, DoctorProfile, PatientProfile, Profile
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.interfaces import LoaderOption

from .base_repository import BaseRepository


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
    CREATED_BY_PROFILE = joinedload(Appointment.created_by)
    CANCELLED_BY_PROFILE = joinedload(Appointment.cancelled_by)


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
        only_include_status_ids: Sequence[int] | None = None,
        datetime_range: tuple[datetime, datetime] | None = None,
        order_by_created_datetime_desc: bool | None = None,
        loaders: Sequence[LoaderOption] = (),
    ) -> Sequence[Appointment]:
        stmt = (
            select(Appointment)
            .where(Appointment.patient_profile_id == patient_profile_id)
            .options(*loaders)
        )

        if only_include_status_ids:
            stmt = stmt.where(
                Appointment.appointment_status_id.in_(only_include_status_ids)
            )
        if datetime_range:
            start, end = datetime_range
            stmt = stmt.where(
                Appointment.start_datetime >= start,
                Appointment.end_datetime <= end,
            )
        if order_by_created_datetime_desc is not None:
            stmt = stmt.order_by(
                Appointment.created_datetime.desc()
                if order_by_created_datetime_desc
                else Appointment.created_datetime.asc()
            )
        return session.scalars(stmt).all()
