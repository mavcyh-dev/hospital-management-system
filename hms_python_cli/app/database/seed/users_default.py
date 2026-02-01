from datetime import date

from app.core.app import Repos, Services
from app.core.config import AppConfig
from app.database.models import (
    AdminProfile,
    Appointment,
    DoctorProfile,
    Medication,
    PatientProfile,
    Profile,
    ReceptionistProfile,
    Specialty,
)
from app.database.seed.utils import (
    generate_random_appointment_requests_for_patients,
    simulate_action_appointment_requests,
    simulate_action_appointments,
)
from app.lookups.enums import ProfileTypeEnum, SexEnum
from faker import Faker
from sqlalchemy import or_, select
from sqlalchemy.orm import Session


def seed_default_users(
    session: Session, seed: int, repos: Repos, services: Services, seed_relations=True
) -> None:
    """Create deterministic system users (patient, doctor, receptionist, admin)."""
    fake = Faker()
    fake.seed_instance(seed)

    print(
        "[seed] Creating 'patient', 'doctor', 'receptionist', 'admin' profiles with user and person (password: 'password')..."
    )
    patient_user = services.user.create_user_and_person(
        session=session,
        username="patient",
        plain_password="password",
        first_name="Alice",
        last_name="Johnson",
        date_of_birth=date(1980, 1, 1),
        primary_email="patient@nyphospital.com",
        primary_phone_number="+65 9222 3333",
        primary_home_address="NYP School",
        sex=SexEnum.FEMALE,
    )
    patient_profile = repos.profile.add(
        session,
        Profile(
            person_id=patient_user.person_id, profile_type_id=ProfileTypeEnum.PATIENT
        ),
    )
    patient_patient_profile = repos.patient_profile.add(
        session,
        PatientProfile(
            profile_id=patient_profile.profile_id, medication_allergies="Penicillin"
        ),
    )

    doctor_user = services.user.create_user_and_person(
        session=session,
        username="doctor",
        plain_password="password",
        first_name="Johnny",
        last_name="Sins",
        date_of_birth=date(1980, 5, 15),
        primary_email="doctor@hospital.com",
        primary_phone_number="+65 9222 3333",
        primary_home_address="NYP Hospital",
        sex=SexEnum.MALE,
    )
    doctor_profile = repos.profile.add(
        session,
        Profile(
            person_id=doctor_user.person_id,
            profile_type_id=ProfileTypeEnum.DOCTOR,
        ),
    )
    doctor_doctor_profile = repos.doctor_profile.add(
        session,
        DoctorProfile(
            profile_id=doctor_profile.profile_id, office_phone_number="+65 6677 8899"
        ),
    )

    doctor_profile = repos.profile.add(
        session,
        Profile(
            person_id=doctor_user.person_id,
            profile_type_id=ProfileTypeEnum.PATIENT,
        ),
    )
    doctor_patient_profile = repos.patient_profile.add(
        session,
        PatientProfile(
            profile_id=doctor_profile.profile_id,
            medication_allergies="Aspirin, Naproxen (mild)",
        ),
    )

    receptionist_user = services.user.create_user_and_person(
        session=session,
        username="receptionist",
        plain_password="password",
        first_name="Jane",
        last_name="Doe",
        date_of_birth=date(1995, 8, 20),
        primary_email="receptionist@nyphospital.com",
        primary_phone_number="+65 9111 2222",
        primary_home_address="NYP Reception",
        sex=SexEnum.FEMALE,
    )
    receptionist_profile = repos.profile.add(
        session,
        Profile(
            person_id=receptionist_user.person_id,
            profile_type_id=ProfileTypeEnum.RECEPTIONIST,
        ),
    )
    receptionist_receptionist_profile = repos.receptionist_profile.add(
        session, ReceptionistProfile(profile_id=receptionist_profile.profile_id)
    )

    admin_user = services.user.create_user_and_person(
        session=session,
        username="admin",
        plain_password="password",
        first_name="System",
        last_name="Administrator",
        date_of_birth=date(1980, 1, 1),
        primary_email="admin@nyphospital.com",
        primary_phone_number="+65 0000 0000",
        primary_home_address="NYP Management",
    )
    admin_profile = repos.profile.add(
        session,
        Profile(person_id=admin_user.person_id, profile_type_id=ProfileTypeEnum.ADMIN),
    )
    admin_admin_profile = repos.admin_profile.add(
        session, AdminProfile(profile_id=admin_profile.profile_id)
    )

    if not seed_relations:
        return

    print(
        "[seed] Simulating events for 'doctor', 'patient', 'receptionist', 'admin'..."
    )
    # "doctor" to have every specialty
    specialties = repos.specialty.get_all(
        session, conditions=[Specialty.is_in_service.is_(True)]
    )
    if not specialties:
        raise ValueError("No specialties found! Ensure that lookup tables are seeded.")
    doctor_doctor_profile.specialties.extend(specialties)

    # "patient" to create appointment requests with "doctor"
    appointment_requests = generate_random_appointment_requests_for_patients(
        fake,
        [patient_patient_profile],
        [doctor_doctor_profile],
        peak_count=100,
        min_count=80,
        max_count=120,
        preferred_datetime_max_days_aft_creation=AppConfig.appointment_preferred_datetime_max_days_from_current,
    )
    session.add_all(appointment_requests)
    session.flush()

    # "patient" to have appointments with "doctor" that were handled by "receptionist"
    # "patient" can also possibly reject or cancel his appointments
    simulate_action_appointment_requests(
        session,
        fake,
        appointment_requests,
        [receptionist_receptionist_profile],
        [doctor_doctor_profile],
    )

    stmt = select(Appointment).where(
        or_(
            Appointment.patient_profile_id == patient_patient_profile.profile_id,
            Appointment.doctor_profile_id == doctor_doctor_profile.profile_id,
        )
    )
    appointments = session.scalars(stmt).all()
    medications = session.scalars(select(Medication)).all()
    simulate_action_appointments(
        session,
        fake,
        appointments,
        medications,
        AppConfig.appointment_min_days_from_start_allow_cancel,
    )
