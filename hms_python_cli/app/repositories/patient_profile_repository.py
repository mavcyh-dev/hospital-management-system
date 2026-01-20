from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from app.database.models import PatientProfile, Profile, Person
from .base_repository import BaseRepository


class PatientProfileRepository(BaseRepository[PatientProfile]):
    def __init__(self):
        super().__init__(PatientProfile)

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------

    def get_with_profile_and_person(
        self, session: Session, profile_id: int
    ) -> PatientProfile | None:
        """Retrieve a patient profile with profile and person details eagerly loaded."""
        stmt = (
            select(PatientProfile)
            .options(joinedload(PatientProfile.profile).joinedload(Profile.person))
            .where(PatientProfile.profile_id == profile_id)
        )
        return session.scalar(stmt)

    def get_by_person_id(
        self, session: Session, person_id: int
    ) -> PatientProfile | None:
        """Retrieve a patient profile by person_id."""
        stmt = (
            select(PatientProfile)
            .join(PatientProfile.profile)
            .where(Profile.person_id == person_id)
        )
        return session.scalar(stmt)

    def get_by_person_id_with_details(
        self, session: Session, person_id: int
    ) -> PatientProfile | None:
        """Retrieve a patient profile by person_id with all details eagerly loaded."""
        stmt = (
            select(PatientProfile)
            .join(PatientProfile.profile)
            .options(joinedload(PatientProfile.profile).joinedload(Profile.person))
            .where(Profile.person_id == person_id)
        )
        return session.scalar(stmt)

    def list_all_active(self, session: Session) -> list[PatientProfile]:
        """List all active patient profiles (is_in_service=True)."""
        stmt = (
            select(PatientProfile)
            .join(PatientProfile.profile)
            .where(Profile.is_in_service == True)
            .options(joinedload(PatientProfile.profile).joinedload(Profile.person))
        )
        return list(session.scalars(stmt))

    def exists_for_person(self, session: Session, person_id: int) -> bool:
        """Check if a patient profile exists for a given person."""
        stmt = (
            select(PatientProfile.profile_id)
            .join(PatientProfile.profile)
            .where(Profile.person_id == person_id)
            .limit(1)
        )
        return session.scalar(stmt) is not None
