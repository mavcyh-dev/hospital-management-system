from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.repositories import PatientProfileRepository, PersonRepository

from app.services.base_service import BaseService
from app.database.models import Profile, PatientProfile

from app.lookups.enums import ProfileTypeEnum


class PatientService(BaseService[PatientProfile]):
    def __init__(
        self,
        patient_profile_repo: PatientProfileRepository,
        person_repo: PersonRepository,
    ):
        super().__init__(patient_profile_repo)
        self.patient_profile_repo = patient_profile_repo
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
        if self.patient_profile_repo.exists_for_person(session, person_id):
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
        return self.patient_profile_repo.add(session, patient_profile)

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------

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
        patient = self.patient_profile_repo.get(session, profile_id)
        if not patient:
            raise ValueError(f"Patient profile with id {profile_id} not found")

        patient.medication_allergies = medication_allergies
        return self.patient_profile_repo.update(session, patient)

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
        patient = self.patient_profile_repo.get(session, profile_id)
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
