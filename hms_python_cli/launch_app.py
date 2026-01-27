import argparse
import sys
import traceback
from pathlib import Path

from app.core.app import App, Repos, Services
from app.database.engine import MySQLDatabase, SQLiteDatabase
from app.database.models import (
    AdminProfile,
    Base,
    Medication,
    Profile,
    ReceptionistProfile,
    Specialty,
)
from app.database.seed import seed_all, seed_all_with_random_users
from app.repositories import (
    AppointmentRepository,
    AppointmentRequestRepository,
    BaseRepository,
    DoctorProfileRepository,
    PatientProfileRepository,
    PersonRepository,
    PrescriptionRepository,
    UserRepository,
)
from app.services import (
    AppointmentService,
    DoctorService,
    PatientService,
    PersonService,
    SecurityService,
    UserService,
)

DB_PATH = (Path(sys.argv[0]).parent / "app.db").resolve()
SCHEMA_NAME = "nyp_hms"
SEEDING_NUMBER = 10

parser = argparse.ArgumentParser()
parser.add_argument("--mysql", action="store_true")
parser.add_argument("--sqlite", action="store_true")
parser.add_argument("--reset", action="store_true")
parser.add_argument("--seed", action="store_true")
parser.add_argument("--seed-random-users", action="store_true")

args = parser.parse_args()
mysql: bool = args.mysql
sqlite: bool = args.sqlite
reset: bool = args.reset
seed: bool = args.seed
seed_random_users: bool = args.seed_random_users


def main():
    try:
        if sqlite:
            if reset and DB_PATH.exists():
                DB_PATH.unlink()
            db = SQLiteDatabase(db_path=DB_PATH)
            Base.metadata.create_all(db.engine)
        elif mysql:
            db = MySQLDatabase(password="!password", database=SCHEMA_NAME)
            if reset:
                Base.metadata.drop_all(db.engine)
            Base.metadata.create_all(db.engine)
        else:
            raise ValueError("Select either --sqlite or --mysql.")

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
            prescription_repo=prescription_repo,
        )

        services = Services(
            security=security_service,
            user=user_service,
            person=person_service,
            patient=patient_service,
            doctor=doctor_service,
            appointment=appointment_service,
        )

        if seed_random_users:
            seed_all_with_random_users(db, repos, services, SEEDING_NUMBER)
        elif seed:
            seed_all(db, repos, services, SEEDING_NUMBER)

        app = App(db=db, repos=repos, services=services)

    except Exception as e:
        print(f"Unhandled exception during app startup: {e}")
        traceback.print_exc()
        input("Press ENTER to exit.")
        return

    app.run()


if __name__ == "__main__":
    main()
