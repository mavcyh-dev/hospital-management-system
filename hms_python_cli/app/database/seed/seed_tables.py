from datetime import datetime, date
import random
from typing import Optional
from faker import Faker
from sqlalchemy.orm import Session

from app.database.models import (
    User,
    Person,
    Profile,
    PatientProfile,
    DoctorProfile,
    ReceptionistProfile,
    AdminProfile,
    Specialty,
)
from app.lookups.enums import ProfileTypeEnum
from app.core.app import Services

faker = Faker()
Faker.seed(123)
random.seed(123)


def seed_tables(session: Session, services: Services) -> None:
    """Seed all main tables with data"""
    create_default_users(session, services)

    patients = generate_patients(session, count=20)
    doctors = generate_doctors(session, count=5)
    receptionists = generate_receptionists(session, count=2)
    admins = generate_admins(session, count=1)

    assign_specialties_to_doctors(session, doctors)


def create_default_user(
    session: Session,
    services: Services,
    username: str,
    password: str,
    profile_type: int,
    profile_detail_class: type,
    first_name: str,
    last_name: str,
    email: str,
    date_of_birth: date = date.today(),
    phone: str = "+65 0000 0000",
    address: str = "NYP Hospital",
    **profile_kwargs,
) -> Optional[User]:
    """Helper to create a complete user with profile

    Returns:
        User object if created, None if user already exists
    """
    # Check if user exists
    existing = session.query(User).filter_by(username=username).first()
    if existing:
        return None

    # Create Person → User → Profile → Profile Detail
    person = Person(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        primary_email=email,
        primary_phone_number=phone,
        primary_home_address=address,
    )
    session.add(person)
    session.flush()

    user = User(
        person_id=person.person_id,
        username=username,
        password_hash=services.security.hash_password(password),
        created_datetime=datetime.now(),
    )
    session.add(user)
    session.flush()

    profile = Profile(
        person_id=person.person_id,
        profile_type_id=profile_type,
        created_datetime=datetime.now(),
    )
    session.add(profile)
    session.flush()

    detail = profile_detail_class(profile_id=profile.profile_id, **profile_kwargs)
    session.add(detail)
    session.flush()

    return user


def create_default_users(session: Session, services: Services) -> None:
    """Create default system users for testing"""
    users_created = []

    # Admin
    if create_default_user(
        session,
        services,
        username="admin",
        password="password",
        profile_type=ProfileTypeEnum.ADMIN,
        profile_detail_class=AdminProfile,
        first_name="System",
        last_name="Administrator",
        email="admin@hospital.com",
    ):
        users_created.append("admin")

    # Doctor
    if create_default_user(
        session,
        services,
        username="doctor",
        password="password",
        profile_type=ProfileTypeEnum.DOCTOR,
        profile_detail_class=DoctorProfile,
        first_name="John",
        last_name="Smith",
        email="dr.smith@hospital.com",
        date_of_birth=date(1980, 5, 15),
        office_phone_number="+65 6677 8899",
    ):
        users_created.append("doctor")

    # Receptionist
    if create_default_user(
        session,
        services,
        username="receptionist",
        password="password",
        profile_type=ProfileTypeEnum.RECEPTIONIST,
        profile_detail_class=ReceptionistProfile,
        first_name="Jane",
        last_name="Doe",
        email="reception@hospital.com",
        date_of_birth=date(1995, 8, 20),
    ):
        users_created.append("receptionist")

    # Patient
    if create_default_user(
        session,
        services,
        username="patient",
        password="password",
        profile_type=ProfileTypeEnum.PATIENT,
        profile_detail_class=PatientProfile,
        first_name="Alice",
        last_name="Johnson",
        email="patient@example.com",
        date_of_birth=date(1985, 3, 10),
        medication_allergies="Penicillin",
    ):
        users_created.append("patient")

    if users_created:
        print(
            f"✓ Created default users: {', '.join(users_created)} (password: 'password')"
        )
    else:
        print("Default users already exist, skipping...")


def create_person(session: Session) -> Person:
    """Create a random person using Faker"""
    person = Person(
        first_name=faker.first_name(),
        last_name=faker.last_name(),
        date_of_birth=faker.date_of_birth(minimum_age=18, maximum_age=90),
        primary_email=faker.unique.email(),
        primary_phone_number=faker.phone_number(),
        primary_home_address=faker.address(),
    )
    session.add(person)
    session.flush()
    return person


def generate_patients(session: Session, count: int) -> list[PatientProfile]:
    """Generate random patient profiles"""
    patients = []
    for _ in range(count):
        person = create_person(session)

        profile = Profile(
            person_id=person.person_id,
            profile_type_id=ProfileTypeEnum.PATIENT,
            created_datetime=datetime.now(),
        )
        session.add(profile)
        session.flush()

        patient = PatientProfile(profile_id=profile.profile_id)
        session.add(patient)
        session.flush()

        patients.append(patient)

    print(f"✓ Created {len(patients)} random patients.")
    return patients


def generate_doctors(session: Session, count: int) -> list[DoctorProfile]:
    """Generate random doctor profiles"""
    doctors = []
    for _ in range(count):
        person = create_person(session)

        profile = Profile(
            person_id=person.person_id,
            profile_type_id=ProfileTypeEnum.DOCTOR,
            created_datetime=datetime.now(),
        )
        session.add(profile)
        session.flush()

        doctor = DoctorProfile(
            profile_id=profile.profile_id,
            office_phone_number=faker.phone_number(),
        )
        session.add(doctor)
        session.flush()

        doctors.append(doctor)

    print(f"✓ Created {len(doctors)} random doctors.")
    return doctors


def generate_receptionists(session: Session, count: int) -> list[ReceptionistProfile]:
    """Generate random receptionist profiles"""
    receptionists = []
    for _ in range(count):
        person = create_person(session)

        profile = Profile(
            person_id=person.person_id,
            profile_type_id=ProfileTypeEnum.RECEPTIONIST,
            created_datetime=datetime.now(),
        )
        session.add(profile)
        session.flush()

        receptionist = ReceptionistProfile(profile_id=profile.profile_id)
        session.add(receptionist)
        session.flush()

        receptionists.append(receptionist)

    print(f"✓ Created {len(receptionists)} random receptionists.")
    return receptionists


def generate_admins(session: Session, count: int) -> list[AdminProfile]:
    """Generate random admin profiles"""
    admins = []
    for _ in range(count):
        person = create_person(session)

        profile = Profile(
            person_id=person.person_id,
            profile_type_id=ProfileTypeEnum.ADMIN,
            created_datetime=datetime.now(),
        )
        session.add(profile)
        session.flush()

        admin = AdminProfile(profile_id=profile.profile_id)
        session.add(admin)
        session.flush()

        admins.append(admin)

    print(f"✓ Created {len(admins)} random admins.")
    return admins


def assign_specialties_to_doctors(
    session: Session, doctors: list[DoctorProfile]
) -> None:
    """Assign random specialties to doctors with weighted distribution

    Distribution:
    - 70% get 1 specialty
    - 25% get 2 specialties
    - 5% get 3 specialties
    """
    specialties = session.query(Specialty).all()
    if not specialties:
        raise ValueError("No specialties found! Did you seed lookup tables first?")

    for doctor in doctors:
        # Weighted choice: 1 specialty = 70%, 2 = 25%, 3 = 5%
        num_specialties = random.choices(
            population=[1, 2, 3], weights=[70, 25, 5], k=1
        )[0]

        # Don't sample more than available specialties
        num_specialties = min(num_specialties, len(specialties))

        chosen = random.sample(specialties, k=num_specialties)
        doctor.specialties.extend(chosen)

    print(f"✓ Assigned specialties to {len(doctors)} doctors.")
