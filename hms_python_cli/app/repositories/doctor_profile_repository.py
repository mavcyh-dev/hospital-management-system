from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from app.database.models import DoctorProfile, Profile, Person, Specialty
from .base_repository import BaseRepository


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

    def get_with_profile_and_person(
        self, session: Session, profile_id: int
    ) -> DoctorProfile | None:
        """Retrieve a doctor profile with profile and person details eagerly loaded."""
        stmt = (
            select(DoctorProfile)
            .options(joinedload(DoctorProfile.profile).joinedload(Profile.person))
            .where(DoctorProfile.profile_id == profile_id)
        )
        return session.scalar(stmt)

    def get_with_specialties(
        self, session: Session, profile_id: int
    ) -> DoctorProfile | None:
        """Retrieve a doctor profile with specialties eagerly loaded."""
        stmt = (
            select(DoctorProfile)
            .options(
                joinedload(DoctorProfile.specialties),
                joinedload(DoctorProfile.profile).joinedload(Profile.person),
            )
            .where(DoctorProfile.profile_id == profile_id)
        )
        return session.scalar(stmt)

    def get_by_person_id(
        self, session: Session, person_id: int
    ) -> DoctorProfile | None:
        """Retrieve a doctor profile by person_id."""
        stmt = (
            select(DoctorProfile)
            .join(DoctorProfile.profile)
            .where(Profile.person_id == person_id)
        )
        return session.scalar(stmt)

    def get_by_person_id_with_details(
        self, session: Session, person_id: int
    ) -> DoctorProfile | None:
        """Retrieve a doctor profile by person_id with all details eagerly loaded."""
        stmt = (
            select(DoctorProfile)
            .join(DoctorProfile.profile)
            .options(
                joinedload(DoctorProfile.specialties),
                joinedload(DoctorProfile.profile).joinedload(Profile.person),
            )
            .where(Profile.person_id == person_id)
        )
        return session.scalar(stmt)

    def list_by_specialty(
        self, session: Session, specialty_id: int, active_only: bool = True
    ) -> list[DoctorProfile]:
        """List all doctors with a specific specialty.

        Args:
            session: Database session
            specialty_id: ID of the specialty to filter by
            active_only: Only return doctors with is_in_service=True

        Returns:
            List of DoctorProfile records with that specialty
        """
        stmt = (
            select(DoctorProfile)
            .join(DoctorProfile.specialties)
            .join(DoctorProfile.profile)
            .where(Specialty.specialty_id == specialty_id)
            .options(
                joinedload(DoctorProfile.specialties),
                joinedload(DoctorProfile.profile).joinedload(Profile.person),
            )
        )

        if active_only:
            stmt = stmt.where(
                Profile.is_in_service == True, Specialty.is_in_service == True
            )

        return list(
            session.scalars(stmt).unique()
        )  # unique() needed for joinedload with many-to-many

    def list_by_specialty_name(
        self, session: Session, specialty_name: str, active_only: bool = True
    ) -> list[DoctorProfile]:
        """List all doctors with a specific specialty by name.

        Args:
            session: Database session
            specialty_name: Name of the specialty (e.g., "Cardiology")
            active_only: Only return doctors with is_in_service=True

        Returns:
            List of DoctorProfile records with that specialty
        """
        stmt = (
            select(DoctorProfile)
            .join(DoctorProfile.specialties)
            .join(DoctorProfile.profile)
            .where(Specialty.name == specialty_name)
            .options(
                joinedload(DoctorProfile.specialties),
                joinedload(DoctorProfile.profile).joinedload(Profile.person),
            )
        )

        if active_only:
            stmt = stmt.where(
                Profile.is_in_service == True, Specialty.is_in_service == True
            )

        return list(session.scalars(stmt).unique())

    def list_all_active(self, session: Session) -> list[DoctorProfile]:
        """List all active doctor profiles with person and specialty details."""
        stmt = (
            select(DoctorProfile)
            .join(DoctorProfile.profile)
            .where(Profile.is_in_service == True)
            .options(
                joinedload(DoctorProfile.specialties),
                joinedload(DoctorProfile.profile).joinedload(Profile.person),
            )
        )
        return list(session.scalars(stmt).unique())
