from datetime import datetime, date
from sqlalchemy.orm import Session

from app.database.models import DoctorProfile
from app.repositories.user_repository import UserRepository
from app.repositories.person_repository import PersonRepository
from app.repositories.doctor_profile_repository import DoctorProfileRepository
from app.services.base_service import BaseService


class DoctorService(BaseService[DoctorProfile]):
    def __init__(
        self,
        doctor_profile_repo: DoctorProfileRepository,
        user_repo: UserRepository,
        person_repo: PersonRepository,
    ):
        super().__init__(doctor_profile_repo)
        self.doctor_profile_repo = (doctor_profile_repo,)
        self.user_repo = user_repo
        self.person_repo = person_repo

    # -------------------------------------------------------------------------
    # CREATE
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # DELETE / DEACTIVATE
    # -------------------------------------------------------------------------
