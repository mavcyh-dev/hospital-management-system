from collections import OrderedDict
from datetime import datetime, timedelta
from typing import List, Sequence

from app.core.config import AppConfig
from app.database.models import (
    AdminProfile,
    Appointment,
    DoctorProfile,
    Medication,
    PatientProfile,
    Person,
    Profile,
    ReceptionistProfile,
    Specialty,
    User,
)
from app.database.seed.utils import (
    generate_random_appointment_requests_for_patients,
    simulate_action_appointment_requests,
    simulate_action_appointments,
)
from app.lookups.enums import ProfileTypeEnum, SexEnum
from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload


def seed_users_random(
    session: Session,
    seed: int,
    patients_count: int,
    doctors_count: int,
    receptionists_count: int,
    admins_count: int,
) -> None:

    fake = Faker()
    fake.seed_instance(seed)

    print(
        f"[seed] Creating {patients_count} patients, {doctors_count} doctors, {receptionists_count} receptionists, {admins_count} admins (password: 'password')..."
    )

    patients: list[PatientProfile] = _generate_user(
        session,
        fake,
        count=patients_count,
        profile_type=ProfileTypeEnum.PATIENT,
        profile_cls=PatientProfile,
    )
    doctors: Sequence[DoctorProfile] = _generate_user(
        session,
        fake,
        count=doctors_count,
        profile_type=ProfileTypeEnum.DOCTOR,
        profile_cls=DoctorProfile,
        doctor_office_phone=True,
    )
    receptionists: Sequence[ReceptionistProfile] = _generate_user(
        session,
        fake,
        count=receptionists_count,
        profile_type=ProfileTypeEnum.RECEPTIONIST,
        profile_cls=ReceptionistProfile,
    )
    admins: Sequence[AdminProfile] = _generate_user(
        session,
        fake,
        count=admins_count,
        profile_type=ProfileTypeEnum.ADMIN,
        profile_cls=AdminProfile,
    )
    session.commit()

    print("[seed] Assigning random specialties to doctors...")
    specialties = session.scalars(select(Specialty)).all()
    doctors = session.scalars(select(DoctorProfile).options()).all()
    for doctor in doctors:
        num_specialties = fake.random_element(
            elements=OrderedDict([(1, 70), (2, 25), (3, 5)])
        )
        num_specialties = min(num_specialties, len(specialties))
        doctor.specialties.extend(
            fake.random_elements(
                elements=specialties,
                length=num_specialties,
                unique=True,
            )
        )
    session.commit()

    print("[seed] Creating appointment requests...")
    doctors = session.scalars(
        select(DoctorProfile).options(selectinload(DoctorProfile.specialties))
    ).all()
    appointment_requests = generate_random_appointment_requests_for_patients(
        fake,
        patients,
        doctors,
        creation_datetime_max_days_bef_current=365,
        preferred_datetime_max_days_aft_creation=AppConfig.appointment_preferred_datetime_max_days_from_current,
    )
    session.add_all(appointment_requests)
    session.flush()

    print("[seed] Simulating actions on created appointment requests...")
    simulate_action_appointment_requests(
        session,
        fake,
        appointment_requests,
        receptionists,
        doctors,
        handled_datetime_min_days_bef_preferred=21,
        handled_datetime_max_days_aft_created=7,
    )

    print("[seed] Simulating actions on created appointments...")
    appointments = session.scalars(select(Appointment)).all()
    medications = session.scalars(select(Medication)).all()
    simulate_action_appointments(
        session, fake, appointments, medications, max_days_before_cancellation=2
    )


def _generate_user(
    session: Session,
    fake: Faker,
    count: int,
    profile_type: ProfileTypeEnum,
    profile_cls,
    doctor_office_phone: bool = False,
) -> List:
    created = []
    batch_size = 300

    for i in range(count):
        person, profile = _create_person_and_profile(session, fake, profile_type, i)

        kwargs = {}
        if doctor_office_phone:
            kwargs["office_phone_number"] = fake.numerify("+65 6### ####")

        detail = profile_cls(profile_id=profile.profile_id, **kwargs)
        session.add(detail)
        created.append(detail)

        if (i + 1) % batch_size == 0:
            session.flush()
            session.commit()

    session.flush()
    session.commit()
    return created


def _create_person_and_profile(
    session: Session,
    fake: Faker,
    profile_type: ProfileTypeEnum,
    iteration_count: int,
):
    username = f"{str(profile_type.display).lower()}{iteration_count}"

    min_age = 0 if profile_type == ProfileTypeEnum.PATIENT else 22
    date_of_birth = fake.date_of_birth(minimum_age=min_age, maximum_age=100)
    person = Person(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        sex=fake.random_element([SexEnum.MALE.value, SexEnum.FEMALE.value]),
        date_of_birth=date_of_birth,
        primary_email=f"{username}@example.com",
        primary_phone_number=fake.numerify("+65 9### ####"),
        primary_home_address=fake.address(),
    )
    session.add(person)
    session.flush()

    current = datetime.now()
    min_creation_date = date_of_birth + timedelta(days=min_age * 365)

    # Hash for string "password" with salt
    DEVELOPMENT_PASSWORD_HASH = (
        "$2b$12$Z42FRYpF93pYTad6xVZcY.JsMq5rM2oT65DTQNKxBv9sxgBXd8ThW"
    )
    created_datetime = fake.date_between_dates(min_creation_date, current)
    user = User(
        person_id=person.person_id,
        username=username,
        password_hash=DEVELOPMENT_PASSWORD_HASH,
        created_datetime=created_datetime,
    )
    session.add(user)
    session.flush()

    profile = Profile(
        person_id=person.person_id,
        profile_type_id=profile_type,
        created_datetime=created_datetime,
    )
    session.add(profile)
    session.flush()

    return person, profile
