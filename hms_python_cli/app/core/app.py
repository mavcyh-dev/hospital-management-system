import traceback
from typing import Callable, ContextManager
from dataclasses import dataclass, field
from datetime import datetime, date
from sqlalchemy import select
from sqlalchemy.orm import Session

from rich.console import Console

from app.database.engine import Database
from app.pages.base_page import BasePage
from app.pages.core.app_start_page import AppStartPage

from app.database.models import Specialty
from app.lookups.enums import ProfileTypeEnum, SexEnum

from app.repositories.user_repository import UserRepository
from app.repositories.person_repository import PersonRepository
from app.repositories.patient_profile_repository import PatientProfileRepository
from app.repositories.doctor_profile_repository import DoctorProfileRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.prescription_repository import PrescriptionRepository
from app.repositories.medication_repository import MedicationRepository

from app.services.security_service import SecurityService
from app.services.user_service import UserService
from app.services.person_service import PersonService
from app.services.patient_service import PatientService
from app.services.doctor_service import DoctorService
from app.services.appointment_service import AppointmentService


@dataclass
class Repos:
    user: UserRepository
    person: PersonRepository
    patient_profile: PatientProfileRepository
    doctor_profile: DoctorProfileRepository
    appointment: AppointmentRepository
    prescription: PrescriptionRepository
    medication: MedicationRepository


@dataclass
class Services:
    security: SecurityService
    user: UserService
    person: PersonService
    patient: PatientService
    doctor: DoctorService
    appointment: AppointmentService


@dataclass
class CurrentUserDTO:
    user_id: int
    username: str
    created_datetime: datetime


@dataclass
class CurrentPersonDTO:
    person_id: int
    sex: SexEnum
    first_name: str
    last_name: str
    date_of_birth: date
    primary_email: str
    primary_phone_number: str
    primary_home_address: str


@dataclass
class LookupCache:
    specialties: dict[int, str] = field(default_factory=dict)
    specialties_by_name: dict[str, int] = field(default_factory=dict)

    def load_from_database(self, session: Session) -> None:
        """Load specialties from database into cache"""
        stmt = select(Specialty).where(Specialty.is_in_service == True)
        specialties = session.scalars(stmt).all()

        self.specialties = {s.specialty_id: s.name for s in specialties}
        self.specialties_by_name = {s.name: s.specialty_id for s in specialties}

        print(f"✓ Loaded {len(self.specialties)} specialties into cache")

    def get_specialty_name(self, specialty_id: int) -> str | None:
        """Get specialty name by ID (from cache)"""
        return self.specialties.get(specialty_id)

    def get_specialty_id(self, name: str) -> int | None:
        """Get specialty ID by name (from cache)"""
        return self.specialties_by_name.get(name)

    def get_all_specialties(self) -> list[tuple[int, str]]:
        """Get all specialties as [(id, name), ...] for UI display"""
        return sorted(self.specialties.items(), key=lambda x: x[1])

    def reload(self, session: Session) -> None:
        """Reload cache (after admin adds/updates specialties)"""
        self.load_from_database(session)


class App:
    """Main application class with dependency injection"""

    console: Console
    db: Database
    session_scope: Callable[[], ContextManager[Session]]
    repos: Repos
    services: Services
    lookup_cache: LookupCache
    current_user: CurrentUserDTO | None
    current_person: CurrentPersonDTO | None
    current_profile_type: ProfileTypeEnum | None

    def __init__(
        self,
        db: Database,
        repos: Repos,
        services: Services,
    ):
        self.console = Console()
        self.db = db
        self.session_scope = db.session_scope
        self.repos = repos
        self.services = services

        self.lookup_cache = LookupCache()
        with self.session_scope() as session:
            self.lookup_cache.load_from_database(session)

        # Session state
        self.current_user = None
        self.current_person = None
        self.current_profile_type = None

        # Page navigation
        self._start_page: BasePage = AppStartPage(self)
        self._page_stack: list[BasePage] = [self._start_page]
        self._logged_in: bool = False

    def run(self):
        """Main application loop"""
        try:
            while self._page_stack:
                page = self._page_stack[-1]
                result = page.run()

                if result is None:
                    self._page_stack.pop()
                else:
                    self._page_stack.append(result)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Application interrupted by user.[/]")
        except Exception:
            self.console.print("\n[red]Unexpected error in app.[/]")
            traceback.print_exc()
            try:
                input("Press ENTER to exit.")
            except EOFError:
                pass
        finally:
            self.db.close()

    def login(
        self,
        current_user: CurrentUserDTO,
        current_person: CurrentPersonDTO,
        current_profile_type: ProfileTypeEnum,
    ):
        self.current_user = current_user
        self.current_person = current_person
        self.current_profile_type = current_profile_type

        self._logged_in = True

        self._page_stack.clear()

    def logout(self):
        self.current_user = None
        self.current_person = None
        self.current_profile_type = None

        self._logged_in = False

        current_page = self._page_stack[-1]
        self._page_stack.clear()
        self._page_stack.append(self._start_page)
        self._page_stack.append(current_page)
