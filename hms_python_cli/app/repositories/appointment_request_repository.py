from typing import Sequence
from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.interfaces import LoaderOption
from sqlalchemy import select

from app.database.models import (
    AppointmentRequest,
    Profile,
    PatientProfile,
    DoctorProfile,
)
from .base_repository import BaseRepository

from app.lookups.enums import AppointmentRequestStatusEnum


class AppointmentRequestLoad:
    SPECIALTY = joinedload(AppointmentRequest.specialty)
    PREFERRED_DOCTOR_WITH_PERSON = (
        joinedload(AppointmentRequest.preferred_doctor)
        .joinedload(DoctorProfile.profile)
        .joinedload(Profile.person)
    )
    PATIENT_WITH_PERSON = (
        joinedload(AppointmentRequest.patient)
        .joinedload(PatientProfile.profile)
        .joinedload(Profile.person)
    )


class AppointmentRequestRepository(BaseRepository[AppointmentRequest]):
    def __init__(self):
        super().__init__(AppointmentRequest)

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
        loaders: Sequence[LoaderOption] = (),
    ) -> Sequence[AppointmentRequest]:
        stmt = (
            select(AppointmentRequest)
            .where(AppointmentRequest.patient_profile_id == patient_profile_id)
            .options(*loaders)
        )

        if only_include_status_ids:
            for status_id in only_include_status_ids:
                stmt = stmt.where(
                    AppointmentRequest.appointment_request_status_id == status_id
                )

        if datetime_range:
            start, end = datetime_range
            stmt = stmt.where(
                AppointmentRequest.created_datetime >= start,
                AppointmentRequest.created_datetime <= end,
            )

        return session.scalars(stmt).all()
