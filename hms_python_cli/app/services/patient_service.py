from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.services.base_service import BaseService
from app.database.models import Profile, PatientProfile
from app.repositories.person_repository import PersonRepository
from app.repositories.patient_profile_repository import PatientProfileRepository
from app.lookups.enums import ProfileTypeEnum


class PatientService(BaseService[PatientProfile]):
    """Service for patient-related operations

    Handles business logic for patient profiles, including creation,
    updates, and validation of patient data.
    """

    def __init__(
        self,
        patient_profile_repo: PatientProfileRepository,
        person_repo: PersonRepository,
    ):
        super().__init__(patient_profile_repo)
        self.patient_repo = patient_profile_repo
        self.person_repo = person_repo

    # -------------------------------------------------------------------------
    # CREATE
    # -------------------------------------------------------------------------

    def create_patient_profile(
        self,
        session: Session,
        person_id: int,
        medication_allergies: str | None = None,
    ) -> PatientProfile:
        """Create a patient profile for an existing person"""
        # Validate person exists
        person = self.person_repo.get(session, person_id)
        if not person:
            raise ValueError(f"Person with id {person_id} not found")

        # Check if patient profile already exists
        if self.patient_exists(session, person_id):
            raise ValueError(f"Patient profile already exists for person {person_id}")

        # Create Profile first
        profile = Profile(
            person_id=person_id,
            profile_type_id=ProfileTypeEnum.PATIENT,
            created_datetime=datetime.now(),
        )
        session.add(profile)
        session.flush()

        # Create PatientProfile
        patient_profile = PatientProfile(
            profile_id=profile.profile_id,
            medication_allergies=medication_allergies,
        )
        return self.patient_repo.add(session, patient_profile)

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------

    def get_patient_by_person_id(
        self, session: Session, person_id: int
    ) -> Optional[PatientProfile]:
        """Get patient profile for a person

        Args:
            session: Database session
            person_id: ID of the person

        Returns:
            PatientProfile if exists, None otherwise
        """
        stmt = (
            select(PatientProfile).join(Profile).where(Profile.person_id == person_id)
        )
        return session.scalar(stmt)

    def get_patient_by_profile_id(
        self, session: Session, profile_id: int
    ) -> Optional[PatientProfile]:
        """Get patient profile by profile ID

        Args:
            session: Database session
            profile_id: ID of the profile

        Returns:
            PatientProfile if exists, None otherwise
        """
        return self.patient_repo.get(session, profile_id)

    def list_all_patients(
        self, session: Session, active_only: bool = True
    ) -> list[PatientProfile]:
        """Get all patient profiles

        Args:
            session: Database session
            active_only: If True, only return patients with is_in_service=True

        Returns:
            List of all PatientProfile records
        """
        stmt = select(PatientProfile).join(Profile)

        if active_only:
            stmt = stmt.where(Profile.is_in_service == True)

        return list(session.scalars(stmt))

    def patient_exists(self, session: Session, person_id: int) -> bool:
        """Check if a patient profile exists for a person

        Args:
            session: Database session
            person_id: ID of the person to check

        Returns:
            True if patient profile exists, False otherwise
        """
        stmt = (
            select(Profile.profile_id)
            .where(
                Profile.person_id == person_id,
                Profile.profile_type_id == ProfileTypeEnum.PATIENT,
            )
            .limit(1)
        )
        return session.scalar(stmt) is not None

    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------

    def update_allergies(
        self,
        session: Session,
        profile_id: int,
        medication_allergies: str | None,
    ) -> PatientProfile:
        """Update patient's medication allergies

        Args:
            session: Database session
            profile_id: ID of the patient profile
            medication_allergies: Updated allergy information

        Returns:
            Updated PatientProfile

        Raises:
            ValueError: If patient profile not found
        """
        patient = self.patient_repo.get(session, profile_id)
        if not patient:
            raise ValueError(f"Patient profile with id {profile_id} not found")

        patient.medication_allergies = medication_allergies
        return self.patient_repo.update(session, patient)

    def change_patient_status(
        self,
        session: Session,
        profile_id: int,
        is_active: bool,
    ) -> PatientProfile:
        """Change patient's active status

        Args:
            session: Database session
            profile_id: ID of the patient profile
            is_active: New status (True=active, False=inactive)

        Returns:
            Updated PatientProfile

        Raises:
            ValueError: If patient profile not found
        """
        patient = self.patient_repo.get(session, profile_id)
        if not patient:
            raise ValueError(f"Patient profile with id {profile_id} not found")

        patient.profile.is_in_service = is_active
        session.flush()
        return patient

    # -------------------------------------------------------------------------
    # DELETE / DEACTIVATE
    # -------------------------------------------------------------------------

    def deactivate_patient(self, session: Session, profile_id: int) -> None:
        """Soft delete a patient by marking their profile as out of service

        Args:
            session: Database session
            profile_id: ID of the patient profile to deactivate

        Raises:
            ValueError: If patient profile not found
        """
        self.change_patient_status(session, profile_id, is_active=False)

    def reactivate_patient(self, session: Session, profile_id: int) -> None:
        """Reactivate a deactivated patient

        Args:
            session: Database session
            profile_id: ID of the patient profile to reactivate

        Raises:
            ValueError: If patient profile not found
        """
        self.change_patient_status(session, profile_id, is_active=True)
