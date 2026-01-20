import traceback
from pathlib import Path
from app.core.app import App, Repos, Services
from app.database.engine import SQLiteDatabase
from app.database.seed.seed_all import seed_all

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


def main():
    app: App

    try:
        db_path = "dev.db"

        if Path(db_path).exists():
            Path(db_path).unlink()

        db = SQLiteDatabase(db_path=db_path)

        # Repositories
        user_repo = UserRepository()
        person_repo = PersonRepository()
        patient_profile_repo = PatientProfileRepository()
        doctor_profile_repo = DoctorProfileRepository()
        appointment_repo = AppointmentRepository()
        prescription_repo = PrescriptionRepository()
        medication_repo = MedicationRepository()

        repos = Repos(
            user=user_repo,
            person=person_repo,
            patient_profile=patient_profile_repo,
            doctor_profile=doctor_profile_repo,
            appointment=appointment_repo,
            prescription=prescription_repo,
            medication=medication_repo,
        )

        # Services
        security_service = SecurityService()
        user_service = UserService(
            user_repo=user_repo,
            person_repo=person_repo,
            security_service=security_service,
        )
        person_service = PersonService(person_repo=person_repo, user_repo=user_repo)
        patient_service = PatientService(
            patient_profile_repo=patient_profile_repo,
            person_repo=person_repo,
        )
        doctor_service = DoctorService(
            doctor_profile_repo=doctor_profile_repo,
            user_repo=user_repo,
            person_repo=person_repo,
        )
        appointment_service = AppointmentService()

        services = Services(
            security=security_service,
            user=user_service,
            person=person_service,
            patient=patient_service,
            doctor=doctor_service,
            appointment=appointment_service,
        )

        seed_all(db, services)

        app = App(db=db, repos=repos, services=services)

    except Exception as e:
        print(f"Unhandled exception during app startup: {e}")
        traceback.print_exc()
        return

    app.run()


if __name__ == "__main__":
    main()
