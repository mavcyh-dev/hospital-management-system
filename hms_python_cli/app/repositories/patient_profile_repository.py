from typing import Sequence

from app.database.models import (
    AppointmentRequest,
    DoctorProfile,
    PatientProfile,
    Profile,
)
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.orm.interfaces import LoaderOption

from .base_repository import BaseRepository


class PatientProfileLoad:
    PROFILE_WITH_PERSON = joinedload(PatientProfile.profile).joinedload(Profile.person)
    APPOINTMENT_REQUESTS = selectinload(PatientProfile.appointment_requests)
    APPOINTMENT_REQUESTS_FULL = (
        joinedload(PatientProfile.appointment_requests).joinedload(
            AppointmentRequest.specialty
        ),
        selectinload(PatientProfile.appointment_requests)
        .joinedload(AppointmentRequest.preferred_doctor)
        .joinedload(DoctorProfile.profile)
        .joinedload(Profile.person),
    )
    APPOINTMENTS = selectinload(PatientProfile.appointments)


class PatientProfileRepository(BaseRepository[PatientProfile]):
    def __init__(self):
        super().__init__(PatientProfile)

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------

    def get_by_id(
        self,
        session: Session,
        profile_id: int,
        *,
        loaders: Sequence[LoaderOption] = (),
    ) -> PatientProfile | None:
        """Retrieve a patient profile with profile and person details eagerly loaded."""
        stmt = (
            select(PatientProfile)
            .options(joinedload(PatientProfile.profile).joinedload(Profile.person))
            .where(PatientProfile.profile_id == profile_id)
            .options(*loaders)
        )
        return session.scalar(stmt)

    def get_by_person_id(
        self,
        session: Session,
        person_id: int,
        *,
        loaders: Sequence[LoaderOption] = (),
    ) -> PatientProfile | None:
        stmt = (
            select(PatientProfile)
            .join(PatientProfile.profile)
            .where(Profile.person_id == person_id)
            .options(*loaders)
        )
        return session.scalar(stmt)

    def list_all_active(
        self,
        session: Session,
        *,
        loaders: Sequence[LoaderOption] = (),
    ) -> list[PatientProfile]:
        stmt = (
            select(PatientProfile)
            .join(PatientProfile.profile)
            .where(Profile.is_in_service.is_(True))
            .options(*loaders)
        )
        return list(session.scalars(stmt))
