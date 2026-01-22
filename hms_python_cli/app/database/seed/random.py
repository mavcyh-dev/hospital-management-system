from __future__ import annotations
from datetime import datetime
import random
import logging
from typing import List

from faker import Faker
from sqlalchemy.orm import Session

from app.database.models import (
    Person,
    Profile,
    PatientProfile,
    DoctorProfile,
    ReceptionistProfile,
    AdminProfile,
    Specialty,
)
from app.lookups.enums import ProfileTypeEnum

log = logging.getLogger(__name__)
fake = Faker()
Faker.seed(123)
random.seed(123)


def seed_random(
    session: Session,
    patients: int = 1000,
    doctors: int = 500,
    receptionists: int = 30,
    admins: int = 0,
) -> None:
    """
    Fast, ORM-based bulk seeding for many entities.

    NOTE: For very large numbers you might want to switch to bulk_insert_mappings
    for Persons then do a second pass to create profiles. This version uses flush()
    to keep FK creation straightforward and readable.
    """
    log.info(
        "Starting random seeding: %d patients, %d doctors, %d receptionists, %d admins",
        patients,
        doctors,
        receptionists,
        admins,
    )

    patient_objs = _generate_profiles(
        session,
        count=patients,
        profile_type=ProfileTypeEnum.PATIENT,
        profile_cls=PatientProfile,
    )
    doctor_objs = _generate_profiles(
        session,
        count=doctors,
        profile_type=ProfileTypeEnum.DOCTOR,
        profile_cls=DoctorProfile,
        doctor_office_phone=True,
    )
    receptionist_objs = _generate_profiles(
        session,
        count=receptionists,
        profile_type=ProfileTypeEnum.RECEPTIONIST,
        profile_cls=ReceptionistProfile,
    )
    admin_objs = _generate_profiles(
        session,
        count=admins,
        profile_type=ProfileTypeEnum.ADMIN,
        profile_cls=AdminProfile,
    )

    session.commit()
    log.info(
        "Random seeding created: %d patients, %d doctors, %d receptionists, %d admins",
        len(patient_objs),
        len(doctor_objs),
        len(receptionist_objs),
        len(admin_objs),
    )

    assign_specialties_to_doctors(session, doctor_objs)


def _create_person_and_profile(
    session: Session, profile_type: int
) -> tuple[Person, Profile]:
    """Create a Person and Profile and return them (with flushed IDs)."""
    p = Person(
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        date_of_birth=fake.date_of_birth(minimum_age=22, maximum_age=80),
        primary_email=f"{fake.user_name()}{random.randint(1,10000)}@example.com",
        primary_phone_number=fake.unique.numerify("+65 9### ####"),
        primary_home_address=fake.address(),
        is_in_service=True,
    )
    session.add(p)
    session.flush()

    prof = Profile(
        person_id=p.person_id,
        profile_type_id=profile_type,
        created_datetime=datetime.now(),
        is_in_service=True,
    )
    session.add(prof)
    session.flush()

    return p, prof


def _generate_profiles(
    session: Session,
    count: int,
    profile_type: int,
    profile_cls,
    doctor_office_phone: bool = False,
) -> List:
    created = []
    batch_size = 200
    for i in range(count):
        p, prof = _create_person_and_profile(session, profile_type)
        kwargs = {}
        if doctor_office_phone:
            kwargs["office_phone_number"] = fake.unique.numerify("+65 6### ####")

        detail = profile_cls(profile_id=prof.profile_id, **kwargs)
        session.add(detail)

        # flush / commit periodically to avoid huge transactions
        if (i + 1) % batch_size == 0:
            session.flush()
            session.commit()

        created.append(detail)

    # final flush & commit
    session.flush()
    session.commit()
    return created


def assign_specialties_to_doctors(
    session: Session, doctors: List[DoctorProfile]
) -> None:
    """Randomly assign specialties to doctor objects (list of DoctorProfile instances)."""
    specialties = session.query(Specialty).filter_by(is_in_service=True).all()
    if not specialties:
        raise ValueError("No specialties found! Ensure that lookup tables are seeded.")

    for doctor in doctors:
        # Weighted choice: 1 specialty = 70%, 2 = 25%, 3 = 5%
        num = random.choices(population=[1, 2, 3], weights=[70, 25, 5], k=1)[0]
        num = min(num, len(specialties))
        chosen = random.sample(specialties, k=num)
        # doctor.specialties is a relationship list — extend with chosen Specialty ORM objects
        doctor.specialties.extend(chosen)

    session.commit()
    log.info("Assigned specialties to %d doctors", len(doctors))
