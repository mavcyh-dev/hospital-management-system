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

SQLITE_DB_PATH = (Path(sys.argv[0]).parent / "app.db").resolve()
MY_SQL_SCHEMA_NAME = "nyp_hms"
SEEDING_NUMBER = 10

parser = argparse.ArgumentParser()
parser.add_argument("--mysql", action="store_true")
parser.add_argument("--sqlite", action="store_true")
parser.add_argument("--no-reset", action="store_true")
parser.add_argument("--reset", action="store_true")
parser.add_argument("--no-seed", action="store_true")
parser.add_argument("--seed", action="store_true")
parser.add_argument("--seed-random-users", action="store_true")

args = parser.parse_args()
mysql: bool = args.mysql
sqlite: bool = args.sqlite
no_reset: bool = args.no_reset
reset: bool = args.reset
no_seed: bool = args.no_seed
seed: bool = args.seed
seed_random_users: bool = args.seed_random_users

# If not using .bat launch files and using auto-runners without arguments

# None | "mysql", "sqlite"
OVERRIDE_DB_TYPE = None
# None | True, False
OVERRIDE_RESET = None
# None | "no_seed", "seed", "seed_random_users"
OVERRIDE_SEED_TYPE = None


def main():
    try:
        if OVERRIDE_DB_TYPE:
            db_type = OVERRIDE_DB_TYPE
            print("[app] OVERRIDE_DB_TYPE set to MySQL.")
        elif mysql:
            db_type = "mysql"
        elif sqlite:
            db_type = "sqlite"
        else:
            print("[app] --sqlite / --mysql was not provided. Defaulting to MySQL.")
            db_type = "mysql"

        if OVERRIDE_RESET:
            perform_reset = OVERRIDE_RESET
        elif reset:
            perform_reset = True
        if no_reset:
            perform_reset = False
        else:
            print("[app] --no-reset / --reset was not provided. Defaulting to reset.")
            perform_reset = True

        if OVERRIDE_SEED_TYPE:
            seed_type = OVERRIDE_SEED_TYPE
        elif no_seed:
            seed_type = "no_seed"
        elif seed:
            seed_type = "seed"
        elif seed_random_users:
            seed_type = "seed_random_users"
        else:
            print(
                "[app] --no-seed / --seed / --seed-random-users was not provided. Defaulting to seed random users."
            )
            seed_type = "seed_random_users"

        if db_type == "sqlite":
            if perform_reset and SQLITE_DB_PATH.exists():
                SQLITE_DB_PATH.unlink()
            db = SQLiteDatabase(db_path=SQLITE_DB_PATH)
            Base.metadata.create_all(db.engine)
        elif db_type == "mysql":
            db = MySQLDatabase(password="!password", database=MY_SQL_SCHEMA_NAME)
            if perform_reset:
                Base.metadata.drop_all(db.engine)
            Base.metadata.create_all(db.engine)
        else:
            raise Exception("db_type was set to an invalid value.")

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
            profile_repo=profile_repo,
            person_repo=person_repo,
        )
        appointment_service = AppointmentService(
            appointment_repo=appointment_repo,
            appointment_request_repo=appointment_request,
            profile_repo=profile_repo,
            patient_profile_repo=patient_profile_repo,
            doctor_profile_repo=doctor_profile_repo,
            receptionist_profile_repo=receptionist_profile_repo,
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

        if seed_type == "seed_random_users":
            seed_all_with_random_users(db, repos, services, SEEDING_NUMBER)
        elif seed_type == "seed":
            seed_all(db, repos, services, SEEDING_NUMBER)
        elif seed_type == "no_seed":
            pass
        else:
            raise Exception("seed_type was set to an invalid value.")

        app = App(db=db, repos=repos, services=services)

    except Exception as e:
        print(f"Unhandled exception during app startup: {e}")
        traceback.print_exc()
        input("Press ENTER to exit.")
        return

    try:
        app.run()
    except Exception as e:
        print(f"Unhandled exception during app runtime: {e}")
        traceback.print_exc()
        input("Press ENTER to exit.")
        return


if __name__ == "__main__":
    main()
