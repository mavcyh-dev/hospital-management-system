# app/database/seed/manual.py
from __future__ import annotations
from datetime import datetime, date, timedelta
from random import randint

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from app.database.models import (
    User,
    Person,
    Profile,
    PatientProfile,
    DoctorProfile,
    ReceptionistProfile,
    AdminProfile,
    Specialty,
    AppointmentRequest,
    Appointment,
    Prescription,
    PrescriptionItem,
    Medication,
)
from app.lookups.enums import ProfileTypeEnum, SexEnum
from app.core.app import Repos, Services


def seed_manual(
    session: Session, repos: Repos, services: Services, seed_relations=True
) -> None:
    """
    Create deterministic system users (patient, doctor, receptionist, admin)."""

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

    doctor_user = services.user.create_user_and_person(
        session=session,
        username="doctor",
        plain_password="password",
        first_name="John",
        last_name="Smith",
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
            person_id=doctor_user.person_id,
            profile_type_id=ProfileTypeEnum.RECEPTIONIST,
        ),
    )

    if not seed_relations:
        session.commit()
        return

    # "doctor" to have every specialty
    specialties = session.scalars(select(Specialty).filter_by(is_in_service=True)).all()
    if not specialties:
        raise ValueError("No specialties found! Ensure that lookup tables are seeded.")
    doctor_doctor_profile.specialties.extend(specialties)

    # "patient" to have appointment requests with "doctor"
    base = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
    timeslots = [base + timedelta(days=i) for i in range(1, 34)]
    appointment_requests: list[AppointmentRequest] = []
    for start in timeslots:
        appointment_request = services.appointment.create_appointment_request(
            session,
            patient_profile_id=patient_patient_profile.profile_id,
            specialty_id=specialties[randint(0, len(specialties) - 1)].specialty_id,
            reason="Seeding appointment request data!",
            preferred_doctor_profile_id=doctor_doctor_profile.profile_id,
            preferred_datetime=start,
        )
        if appointment_request:
            appointment_requests.append(appointment_request)

    # "patient" to have appointments with "doctor"
    base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    appt_slots = [
        base + timedelta(days=0),
        base + timedelta(days=7, hours=2),
        base + timedelta(days=14, hours=4),
    ]
    appointments: list[Appointment] = []
    for start in appt_slots:
        end = start + timedelta(minutes=30)
        appointment = services.appointment.create_appointment(
            session,
            start_datetime=start,
            end_datetime=end,
            patient_profile_id=patient_patient_profile.profile_id,
            doctor_profile_id=doctor_doctor_profile.profile_id,
            specialty_id=specialties[randint(0, len(specialties) - 1)].specialty_id,
            room_name="B.03.123",
            reason="Seeding appointment data!",
            created_by_profile_id=patient_patient_profile.profile_id,
        )
        if appointment:
            appointments.append(appointment)

    if not appointments or not appointments:
        raise Exception("Failed to create appointment/appointment requests.")

    # # Create a prescription for first appointment (if medications exist)
    # med = session.query(Medication).first()
    # if med and created_appointments:
    #     pres = Prescription(
    #         patient_profile_id=patient_profile_id,
    #         doctor_profile_id=doctor_profile_id,
    #         appointment_id=created_appointments[0].appointment_id,
    #         created_datetime=datetime.now(),
    #     )
    #     session.add(pres)
    #     session.flush()

    #     item = PrescriptionItem(
    #         prescription_id=pres.prescription_id,
    #         medication_id=med.medication_id,
    #         instructions="Take one tablet daily (seeded)",
    #     )
    #     session.add(item)
    #     session.commit()
    #     log.info(
    #         "Created a manual prescription with one item for the first appointment."
    #     )
    # else:
    #     log.info(
    #         "No medications found or no appointments created — skipping prescription creation."
    #     )
