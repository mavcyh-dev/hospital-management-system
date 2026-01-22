import traceback
import sys
from pathlib import Path
from app.core.app import App, Repos, Services
from app.database.engine import SQLiteDatabase
from app.database.seed import seed_all

from app.repositories import (
    BaseRepository,
    UserRepository,
    PersonRepository,
    PatientProfileRepository,
    DoctorProfileRepository,
    AppointmentRequestRepository,
    AppointmentRepository,
    PrescriptionRepository,
)

from app.services import (
    SecurityService,
    UserService,
    PersonService,
    PatientService,
    DoctorService,
    AppointmentService,
)

from app.database.models import Profile, Medication

DB_PATH = (Path(sys.argv[0]).parent / "dev.db").resolve()


def main():
    app: App

    try:
        if DB_PATH.exists():
            DB_PATH.unlink()

        db = SQLiteDatabase(db_path=DB_PATH)

        # Repositories
        user_repo = UserRepository()
        person_repo = PersonRepository()
        profile_repo = BaseRepository(Profile)
        patient_profile_repo = PatientProfileRepository()
        doctor_profile_repo = DoctorProfileRepository()
        appointment_request = AppointmentRequestRepository()
        appointment_repo = AppointmentRepository()
        prescription_repo = PrescriptionRepository()
        medication_repo = BaseRepository(Medication)

        repos = Repos(
            user=user_repo,
            person=person_repo,
            profile=profile_repo,
            patient_profile=patient_profile_repo,
            doctor_profile=doctor_profile_repo,
            appointment_request=appointment_request,
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
        appointment_service = AppointmentService(
            appointment_repo=appointment_repo,
            appointment_request_repo=appointment_request,
            patient_profile_repo=patient_profile_repo,
            doctor_profile_repo=doctor_profile_repo,
            user_repo=user_repo,
            person_repo=person_repo,
        )

        services = Services(
            security=security_service,
            user=user_service,
            person=person_service,
            patient=patient_service,
            doctor=doctor_service,
            appointment=appointment_service,
        )

        seed_all(db, repos, services)

        app = App(db=db, repos=repos, services=services)

    except Exception as e:
        print(f"Unhandled exception during app startup: {e}")
        traceback.print_exc()
        input("Press ENTER to exit.")
        return

    app.run()


if __name__ == "__main__":
    main()
