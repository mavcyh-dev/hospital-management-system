from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Sequence

from app.core.config import AppConfig
from app.database.models import (
    Appointment,
    AppointmentRequest,
    DoctorProfile,
    PatientProfile,
    ReceptionistProfile,
    Specialty,
)
from app.lookups.enums import AppointmentRequestStatusEnum, AppointmentStatusEnum
from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session


def generate_random_appointment_requests_for_patients(
    fake: Faker,
    patients: Sequence[PatientProfile],
    doctors: Sequence[DoctorProfile],
    peak_count: int = 4,
    min_count: int = 0,
    max_count: int = 30,
    creation_datetime_max_days_bef_current: int = 365,
    preferred_datetime_max_days_aft_creation: int = 180,
) -> list[AppointmentRequest]:

    appointment_requests: list[AppointmentRequest] = []
    for patient in patients:
        num_requests = fake_biased_int(
            fake, peak=peak_count, min_val=min_count, max_val=max_count
        )
        for _ in range(num_requests):
            preferred_doctor = fake.random_element(doctors)
            specialty = fake.random_element(elements=preferred_doctor.specialties)
            appointment_request = generate_random_appointment_request(
                fake,
                patient,
                preferred_doctor,
                specialty,
                creation_datetime_max_days_bef_current,
                preferred_datetime_max_days_aft_creation,
            )
            appointment_requests.append(appointment_request)
    return appointment_requests


def generate_random_appointment_request(
    fake: Faker,
    patient: PatientProfile,
    preferred_doctor: DoctorProfile,
    specialty: Specialty,
    creation_datetime_max_days_bef_current: int = 365,
    preferred_datetime_max_days_aft_creation: int = 180,
) -> AppointmentRequest:

    current = datetime.now()
    min = current - timedelta(days=creation_datetime_max_days_bef_current)
    created_datetime = fake.date_time_between_dates(min, current)
    preferred_datetime = fake.date_time_between_dates(
        created_datetime,
        created_datetime + timedelta(days=preferred_datetime_max_days_aft_creation),
    )

    return AppointmentRequest(
        patient_profile_id=patient.profile_id,
        specialty_id=specialty.specialty_id,
        reason=fake.sentence(nb_words=30, variable_nb_words=True),
        preferred_doctor_profile_id=(
            preferred_doctor.profile_id if preferred_doctor else None
        ),
        preferred_datetime=preferred_datetime,
        created_datetime=created_datetime,
        appointment_request_status_id=AppointmentRequestStatusEnum.PENDING,
    )


def simulate_action_appointment_requests(
    session: Session,
    fake: Faker,
    appointment_requests: Sequence[AppointmentRequest],
    receptionists: Sequence[ReceptionistProfile],
    doctors: Sequence[DoctorProfile],
    handled_datetime_min_days_bef_preferred: int = 21,
    handled_datetime_max_days_aft_created: int = 7,
):

    for request in appointment_requests:
        if request.status_enum != AppointmentRequestStatusEnum.PENDING:
            continue

        current = datetime.now()

        # Condition 1: Cannot handle until X days after creation
        min_handle_date = request.created_datetime + timedelta(
            days=handled_datetime_max_days_aft_created
        )
        if current < min_handle_date:
            # too early for this request; skip to the next one
            continue

        # Condition 2: Cannot handle until Y days before preferred date
        if request.preferred_datetime:
            earliest_preferred_handle = request.preferred_datetime - timedelta(
                days=handled_datetime_min_days_bef_preferred
            )
            if current < earliest_preferred_handle:
                # too early relative to preferred date; skip
                continue

        handling = fake.random_element(
            OrderedDict([("approve", 60), ("cancel", 20), ("reject", 20)])
        )

        if handling == "approve":
            doctor_selection = fake.random_element(
                OrderedDict([("preferred", 80), ("non_preferred", 20)])
            )
            if doctor_selection == "preferred":
                doctor_id = request.preferred_doctor_profile_id
            else:
                doctor_id = fake.random_element(doctors).profile_id

            busy_appts = [
                (appt.start_datetime, appt.end_datetime)
                for appt in session.scalars(
                    select(Appointment)
                    .where(Appointment.doctor_profile_id == doctor_id)
                    .where(
                        Appointment.appointment_status_id
                        == AppointmentStatusEnum.SCHEDULED
                    )
                )
            ]

            if request.preferred_datetime:
                dt_start = request.preferred_datetime
            else:
                dt_start = request.created_datetime + timedelta(
                    hours=fake_biased_int(fake, peak=240, min_val=24, max_val=960)
                )

            duration_min = fake.random_element(
                OrderedDict([(10, 5), (20, 15), (30, 40), (40, 10), (50, 10), (60, 20)])
            )

            result = random_available_slot(
                fake=fake,
                existing_appts=busy_appts,
                dt_start=dt_start,
                dt_end=dt_start + timedelta(days=2),
                duration_minutes=duration_min,
                interval_minutes=AppConfig.appointment_timeslot_length_minutes,
            )
            if result is None:
                request.cancel()
                continue

            start, end = result

            receptionist = fake.random_element(receptionists)
            appointment = Appointment(
                start_datetime=start,
                end_datetime=end,
                patient_profile_id=request.patient_profile_id,
                doctor_profile_id=doctor_id,  # <- use the selected doctor_id
                specialty_id=request.specialty_id,
                room_name=generate_room_name(
                    fake, max_blocks=6, max_floors=20, max_rooms=400
                ),
                reason=fake.sentence(nb_words=20, variable_nb_words=True),
                appointment_status_id=AppointmentStatusEnum.SCHEDULED,
                created_by_profile_id=receptionist.profile_id,
            )
            session.add(appointment)
            session.flush()

            request.approve(
                appointment_id=appointment.appointment_id,
                handled_by_profile_id=receptionist.profile_id,
            )

            # Set handled_datetime in a sensible range, ensuring it's not in the future
            if request.preferred_datetime:
                earliest = request.preferred_datetime - timedelta(
                    days=handled_datetime_min_days_bef_preferred
                )
                latest = min(current, request.preferred_datetime)
                # if latest < earliest, fallback to earliest
                if latest < earliest:
                    handled_dt = earliest
                else:
                    # pick a random datetime between earliest and latest
                    total_seconds = int((latest - earliest).total_seconds())
                    offset = fake.random_int(0, total_seconds)
                    handled_dt = earliest + timedelta(seconds=offset)
                request.handled_datetime = handled_dt
            else:
                # pick days in [0, handled_datetime_max_days_aft_created]
                days = fake.random_int(min=0, max=handled_datetime_max_days_aft_created)
                request.handled_datetime = request.created_datetime + timedelta(
                    days=days
                )

        elif handling == "cancel":
            request.cancel()

        elif handling == "reject":
            receptionist = fake.random_element(receptionists)
            request.reject(
                handled_by_profile_id=receptionist.profile_id,
                handling_notes=fake.sentence(nb_words=20, variable_nb_words=True),
            )

    session.commit()


def random_available_slot(
    fake: Faker,
    existing_appts: list[tuple[datetime, datetime]],
    dt_start: datetime,
    dt_end: datetime,
    duration_minutes: int = 30,
    interval_minutes: int = 10,
    max_attempts: int = 100,
) -> tuple[datetime, datetime] | None:
    """
    Pick a start/end datetime that doesn't conflict with existing appointments.
    Rounds to nearest interval.
    """
    for _ in range(max_attempts):
        candidate_start = fake.date_time_between(start_date=dt_start, end_date=dt_end)
        # Round to nearest interval
        candidate_start = round_datetime_to_interval(candidate_start, interval_minutes)
        candidate_end = candidate_start + timedelta(minutes=duration_minutes)

        if candidate_end > dt_end:
            continue

        if not is_conflicting(candidate_start, candidate_end, existing_appts):
            return candidate_start, candidate_end
    return None


def round_datetime_to_interval(dt: datetime, interval_minutes: int) -> datetime:
    minutes = (dt.minute // interval_minutes) * interval_minutes
    return dt.replace(minute=minutes, second=0, microsecond=0)


def is_conflicting(
    start: datetime, end: datetime, existing: list[tuple[datetime, datetime]]
) -> bool:
    """Check if a proposed time slot conflicts with any existing slots."""
    for s, e in existing:
        if start < e and end > s:
            return True
    return False


def generate_room_name(
    fake: Faker, max_blocks: int, max_floors: int, max_rooms: int
) -> str:
    """Generate a room name in the format A.01.012"""
    if max_blocks < 1 or max_blocks > 26:
        raise ValueError("max_blocks must be between 1 and 26")
    if max_floors < 1 or max_floors > 99:
        raise ValueError("max_floors must be between 1 and 99")
    if max_rooms < 1 or max_rooms > 999:
        raise ValueError("max_rooms must be between 1 and 999")

    # Block: pick a letter from 'A' up to max_blocks
    block_index = fake.random_int(min=0, max=max_blocks - 1)
    block = chr(ord("A") + block_index)

    # Floor: 1..max_floors, zero-padded
    floor = f"{fake.random_int(min=1, max=max_floors):02d}"

    # Room: 1..max_rooms, zero-padded
    room = f"{fake.random_int(min=1, max=max_rooms):03d}"

    return f"{block}.{floor}.{room}"


def fake_biased_int(
    fake: Faker,
    *,
    peak: int,
    min_val: int,
    max_val: int,
    steepness: float = 2.0,
):
    weights = OrderedDict()
    for i in range(min_val, max_val + 1):
        # weight falls off as we get farther from peak
        weights[i] = max((1 / ((abs(i - peak) + 1) ** steepness)), 0.01)
    return fake.random_element(elements=weights)
