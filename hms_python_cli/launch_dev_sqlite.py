import traceback
import sys
from pathlib import Path
from app.core.app import App, Repos, Services
from app.database.engine import SQLiteDatabase
from app.database.seed import seed_development

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

from app.database.models import (
    Profile,
    ReceptionistProfile,
    AdminProfile,
    Specialty,
    Medication,
)

DB_PATH = (Path(sys.argv[0]).parent / "dev.db").resolve()
SEEDING_NUMBER = 10


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
        receptionist_profile_repo = BaseRepository(ReceptionistProfile)
        admin_profile_repo = BaseRepository(AdminProfile)
        specialty_repo = BaseRepository(Specialty)
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
            receptionist_profile=receptionist_profile_repo,
            admin_profile=admin_profile_repo,
            specialty=specialty_repo,
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
            profile_repo=profile_repo,
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

        seed_development(db, repos, services, SEEDING_NUMBER)

        app = App(db=db, repos=repos, services=services)

    except Exception as e:
        print(f"Unhandled exception during app startup: {e}")
        traceback.print_exc()
        input("Press ENTER to exit.")
        return

    app.run()


if __name__ == "__main__":
    main()
