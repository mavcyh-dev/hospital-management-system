from app.database.models import DoctorProfile, Profile
from app.lookups.enums import ProfileTypeEnum
from app.repositories.base_repository import BaseRepository
from app.repositories.doctor_profile_repository import DoctorProfileRepository
from app.repositories.person_repository import PersonRepository
from app.services.base_service import BaseService
from sqlalchemy.orm import Session


class DoctorService(BaseService[DoctorProfile]):
    def __init__(
        self,
        doctor_profile_repo: DoctorProfileRepository,
        profile_repo: BaseRepository[Profile],
        person_repo: PersonRepository,
    ):
        super().__init__(doctor_profile_repo)
        self.doctor_profile_repo = doctor_profile_repo
        self.profile_repo = profile_repo
        self.person_repo = person_repo

    # -------------------------------------------------------------------------
    # CREATE
    # -------------------------------------------------------------------------

    def create_doctor_profile(
        self,
        session: Session,
        person_id: int,
        office_phone_number: str | None = None,
    ) -> DoctorProfile:
        """Create a doctor profile for an existing person"""
        # Validate person exists
        person = self.person_repo.get(session, person_id)
        if not person:
            raise ValueError(f"Person with id {person_id} not found.")

        # Check if doctor profile already exists
        if self.profile_repo.exists_with_conditions(
            session,
            conditions=[
                Profile.person_id == person_id,
                Profile.profile_type_id == ProfileTypeEnum.DOCTOR,
            ],
        ):
            raise ValueError(f"Doctor profile already exists for person id {person_id}")

        # Create Profile first
        profile = Profile(
            person_id=person_id,
            profile_type_id=ProfileTypeEnum.PATIENT,
        )
        self.profile_repo.add(session, profile)

        # Create DoctorProfile
        doctor_profile = DoctorProfile(
            profile_id=profile.profile_id, office_phone_number=office_phone_number
        )
        return self.doctor_profile_repo.add(session, doctor_profile)

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------
    def update_profile_information(
        self,
        session: Session,
        doctor_profile_id: int,
        office_phone_number: str | None,
    ) -> DoctorProfile:
        doctor = self.doctor_profile_repo.get(session, doctor_profile_id)
        if not doctor:
            raise ValueError(f"Doctor profile with id {doctor_profile_id} not found")

        doctor.office_phone_number = office_phone_number
        return self.doctor_profile_repo.update(session, doctor)

    def change_doctor_status(
        self,
        session: Session,
        doctor_profile_id: int,
        is_active: bool,
    ) -> DoctorProfile:
        doctor = self.doctor_profile_repo.get(session, doctor_profile_id)
        if not doctor:
            raise ValueError(f"Doctor profile with id {doctor_profile_id} not found")

        doctor.profile.is_in_service = is_active
        session.flush()
        return doctor

    # -------------------------------------------------------------------------
    # DELETE / DEACTIVATE
    # -------------------------------------------------------------------------
    def deactivate_doctor(self, session: Session, doctor_profile_id: int) -> None:
        """Soft delete a doctor by marking their profile as out of service"""
        self.change_doctor_status(session, doctor_profile_id, is_active=False)

    def reactivate_doctor(self, session: Session, doctor_profile_id: int) -> None:
        """Reactivate a deactivated doctor"""
        self.change_doctor_status(session, doctor_profile_id, is_active=True)
