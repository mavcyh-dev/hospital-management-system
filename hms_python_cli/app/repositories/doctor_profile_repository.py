from typing import Sequence

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.interfaces import LoaderOption
from sqlalchemy import select

from app.database.models import DoctorProfile, Profile, Specialty
from .base_repository import BaseRepository


class DoctorProfileLoad:
    PERSON = joinedload(DoctorProfile.profile).joinedload(Profile.person)
    SPECIALTIES = joinedload(DoctorProfile.specialties)


class DoctorProfileRepository(BaseRepository[DoctorProfile]):
    """Repository for DoctorProfile operations - pure data access.

    Note: DoctorProfile uses profile_id as its primary key.
    Access pattern: DoctorProfile → Profile → Person
    Many-to-many: DoctorProfile ←→ Specialty (via doctor_specialty table)
    """

    def __init__(self):
        super().__init__(DoctorProfile)

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------

    def get_by_id(
        self,
        session: Session,
        profile_id: int,
        *,
        loaders: Sequence[LoaderOption] = (),
    ) -> DoctorProfile | None:
        """Retrieve a doctor profile with profile and person details eagerly loaded."""
        stmt = (
            select(DoctorProfile)
            .where(DoctorProfile.profile_id == profile_id)
            .options(*loaders)
        )
        return session.scalar(stmt)

    def get_by_person_id(
        self,
        session: Session,
        person_id: int,
        *,
        loaders: Sequence[LoaderOption] = (),
    ) -> DoctorProfile | None:
        stmt = (
            select(DoctorProfile)
            .join(DoctorProfile.profile)
            .where(Profile.person_id == person_id)
            .options(*loaders)
        )
        return session.scalar(stmt)

    def list_by_specialty(
        self,
        session: Session,
        specialty_id: int,
        *,
        active_only: bool = True,
        loaders: Sequence[LoaderOption] = (),
    ) -> list[DoctorProfile]:
        stmt = (
            select(DoctorProfile)
            .join(DoctorProfile.specialties)
            .join(DoctorProfile.profile)
            .where(Specialty.specialty_id == specialty_id)
            .options(*loaders)
        )

        if active_only:
            stmt = stmt.where(
                Profile.is_in_service == True, Specialty.is_in_service == True
            )

        return list(
            session.scalars(stmt).unique()
        )  # unique() needed for joinedload with many-to-many

    def list_all_active(
        self,
        session: Session,
        *,
        loaders: Sequence[LoaderOption] = (),
    ) -> list[DoctorProfile]:
        stmt = (
            select(DoctorProfile)
            .join(DoctorProfile.profile)
            .where(Profile.is_in_service == True)
            .options(*loaders)
        )
        return list(session.scalars(stmt).unique())
