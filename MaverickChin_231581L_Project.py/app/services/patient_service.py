from app.database.models import PatientProfile, Profile
from app.lookups.enums import ProfileTypeEnum
from app.repositories import BaseRepository, PatientProfileRepository, PersonRepository
from app.services.base_service import BaseService
from sqlalchemy.orm import Session


class PatientService(BaseService[PatientProfile]):
    def __init__(
        self,
        patient_profile_repo: PatientProfileRepository,
        profile_repo: BaseRepository[Profile],
        person_repo: PersonRepository,
    ):
        super().__init__(patient_profile_repo)
        self.patient_profile_repo = patient_profile_repo
        self.profile_repo = profile_repo
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
            raise ValueError(f"Person with id {person_id} not found.")

        # Check if patient profile already exists
        if self.profile_repo.exists_with_conditions(
            session,
            conditions=[
                Profile.person_id == person_id,
                Profile.profile_type_id == ProfileTypeEnum.PATIENT,
            ],
        ):
            raise ValueError(
                f"Patient profile already exists for person id {person_id}"
            )

        # Create Profile first
        profile = Profile(
            person_id=person_id,
            profile_type_id=ProfileTypeEnum.PATIENT,
        )
        self.profile_repo.add(session, profile)

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

    def update_profile_information(
        self,
        session: Session,
        patient_profile_id: int,
        medication_allergies: str | None,
    ) -> PatientProfile:
        patient = self.patient_profile_repo.get(session, patient_profile_id)
        if not patient:
            raise ValueError(f"Patient profile with id {patient_profile_id} not found")

        patient.medication_allergies = medication_allergies
        return self.patient_profile_repo.update(session, patient)

    def change_patient_status(
        self,
        session: Session,
        patient_profile_id: int,
        is_active: bool,
    ) -> PatientProfile:
        patient = self.patient_profile_repo.get(session, patient_profile_id)
        if not patient:
            raise ValueError(f"Patient profile with id {patient_profile_id} not found")

        patient.profile.is_in_service = is_active
        session.flush()
        return patient

    # -------------------------------------------------------------------------
    # DELETE / DEACTIVATE
    # -------------------------------------------------------------------------

    def deactivate_patient(self, session: Session, profile_id: int) -> None:
        """Soft delete a patient by marking their profile as out of service"""
        self.change_patient_status(session, profile_id, is_active=False)

    def reactivate_patient(self, session: Session, profile_id: int) -> None:
        """Reactivate a deactivated patient"""
        self.change_patient_status(session, profile_id, is_active=True)
