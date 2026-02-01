from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Sequence

from app.core.config import AppConfig
from app.database.models import (
    Appointment,
    AppointmentRequest,
    DoctorProfile,
    Medication,
    PatientProfile,
    Prescription,
    PrescriptionItem,
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
    peak_count: int = 8,
    min_count: int = 0,
    max_count: int = 80,
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
    preferred_datetime = round_datetime_to_interval(
        preferred_datetime, AppConfig.appointment_timeslot_min_interval_minutes
    )

    return AppointmentRequest(
        patient_profile_id=patient.profile_id,
        specialty_id=specialty.specialty_id,
        reason=fake.sentence(nb_words=20, variable_nb_words=True),
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

        if current < request.created_datetime:
            continue

        # Calculate when this request becomes eligible to be handled
        # (it must be at least created, and we handle within max_days after creation)
        min_handle_date = request.created_datetime
        max_handle_date = request.created_datetime + timedelta(
            days=handled_datetime_max_days_aft_created
        )

        # Only process requests that are past their max handling window
        # (simulating that we're catching up on old requests)
        if current < max_handle_date:
            # Not ready to handle yet
            continue

        # Determine if request should be rejected due to insufficient lead time
        should_reject_due_to_timing = False
        rejection_probability = 0.0

        if request.preferred_datetime:
            days_between_created_and_preferred = (
                request.preferred_datetime - request.created_datetime
            ).days

            # If preferred datetime is too soon after creation
            if (
                days_between_created_and_preferred
                < handled_datetime_min_days_bef_preferred
            ):
                should_reject_due_to_timing = True
                # Scale rejection probability: fewer days = higher rejection chance
                # If 0 days: ~90% reject, if approaching threshold: ~30% reject
                rejection_probability = max(
                    0.3,
                    0.9
                    - (
                        days_between_created_and_preferred
                        / handled_datetime_min_days_bef_preferred
                    )
                    * 0.6,
                )

        # Determine handling action
        if should_reject_due_to_timing:
            # Biased toward rejection
            handling = fake.random_element(
                OrderedDict(
                    [
                        ("reject", int(rejection_probability * 100)),
                        ("approve", int((1 - rejection_probability) * 100)),
                    ]
                )
            )
        else:
            # Normal distribution
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
                interval_minutes=AppConfig.appointment_timeslot_min_interval_minutes,
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
                doctor_profile_id=doctor_id,
                specialty_id=request.specialty_id,
                room_name=generate_room_name(
                    fake, max_blocks=6, max_floors=20, max_rooms=400
                ),
                reason=fake.sentence(nb_words=20, variable_nb_words=True),
                appointment_status_id=AppointmentStatusEnum.SCHEDULED,
                created_by_profile_id=receptionist.profile_id,
            )

            # Set appointment creation datetime (when receptionist created the appointment)
            # This is also when the request was handled
            # Must be: after request creation, before current, within handling window
            earliest = request.created_datetime
            latest = min(current, max_handle_date)

            if latest < earliest:
                # Edge case: use earliest possible
                created_dt = earliest
            else:
                total_seconds = int((latest - earliest).total_seconds())
                if total_seconds > 0:
                    offset = fake.random_int(0, total_seconds)
                    created_dt = earliest + timedelta(seconds=offset)
                else:
                    created_dt = earliest

            # Ensure we never set a future datetime
            if created_dt > current:
                created_dt = current

            appointment.created_datetime = created_dt

            session.add(appointment)
            session.flush()

            # Approve the request
            request.approve(
                appointment_id=appointment.appointment_id,
                handled_by_profile_id=receptionist.profile_id,
            )

            # request.handled_datetime should be same as appointment creation time
            request.handled_datetime = appointment.created_datetime

        elif handling == "cancel":
            # Set handled datetime for cancellation
            earliest = request.created_datetime
            latest = min(current, max_handle_date)

            if latest >= earliest:
                total_seconds = int((latest - earliest).total_seconds())
                if total_seconds > 0:
                    offset = fake.random_int(0, total_seconds)
                    handled_dt = earliest + timedelta(seconds=offset)
                else:
                    handled_dt = earliest
            else:
                handled_dt = earliest

            # Ensure we never set a future datetime
            if handled_dt > current:
                handled_dt = current

            request.handled_datetime = handled_dt
            request.cancel()

        elif handling == "reject":
            receptionist = fake.random_element(receptionists)

            # Set handled datetime for rejection
            earliest = request.created_datetime
            latest = min(current, max_handle_date)

            if latest >= earliest:
                total_seconds = int((latest - earliest).total_seconds())
                if total_seconds > 0:
                    offset = fake.random_int(0, total_seconds)
                    handled_dt = earliest + timedelta(seconds=offset)
                else:
                    handled_dt = earliest
            else:
                handled_dt = earliest

            # Ensure we never set a future datetime
            if handled_dt > current:
                handled_dt = current

            request.handled_datetime = handled_dt
            request.reject(
                handled_by_profile_id=receptionist.profile_id,
                handling_notes=fake.sentence(nb_words=20, variable_nb_words=True),
            )

    session.commit()


def simulate_action_appointments(
    session: Session,
    fake: Faker,
    appointments: Sequence[Appointment],
    medications: Sequence[Medication],
    max_days_before_cancellation: int = 2,
):
    """Simulate appointment outcomes: complete, cancel, or miss appointments."""

    current = datetime.now()

    for appt in appointments:
        if appt.status_enum != AppointmentStatusEnum.SCHEDULED:
            continue

        # Determine the outcome based on timing and randomness
        outcome = None

        # Check if appointment has already passed (should be missed or completed)
        if current > appt.start_datetime:
            # Appointment time has passed - either completed or missed
            outcome = fake.random_element(
                OrderedDict([("completed", 85), ("missed", 15)])
            )
        else:
            # Appointment is in the future - can be cancelled or left scheduled
            days_until_appointment = (appt.start_datetime - current).days

            # Can only cancel if within the cancellation window
            if days_until_appointment <= max_days_before_cancellation:
                # Random outcome: complete (when time comes), cancel, or leave pending
                outcome = fake.random_element(
                    OrderedDict(
                        [
                            ("completed", 60),
                            ("cancelled", 30),
                            ("pending", 10),  # Leave for later simulation
                        ]
                    )
                )
            else:
                # Too far in future, leave it pending
                outcome = "pending"

        if outcome == "pending":
            continue

        if outcome == "completed":
            # Complete the appointment
            appt.complete()

            # Add doctor notes
            appt.doctor_notes = fake.sentence(nb_words=20, variable_nb_words=True)

            # Create prescription with 1-4 medication items
            num_medications = fake.random_element(
                OrderedDict([(1, 30), (2, 40), (3, 20), (4, 10)])
            )

            prescription = Prescription(
                patient_profile_id=appt.patient_profile_id,
                doctor_profile_id=appt.doctor_profile_id,
                appointment_id=appt.appointment_id,
            )

            # Set prescription created_datetime to around appointment end time
            # (doctor writes prescription during or shortly after appointment)
            if current > appt.end_datetime:
                # Appointment already ended, set to shortly after end_datetime
                max_offset_hours = min(
                    24,  # Within 24 hours after appointment
                    int((current - appt.end_datetime).total_seconds() / 3600),
                )
                offset_hours = fake.random_int(0, max_offset_hours)
                prescription.created_datetime = appt.end_datetime + timedelta(
                    hours=offset_hours
                )
            else:
                # Appointment hasn't ended yet (future simulation)
                # Set to end_datetime for now
                prescription.created_datetime = appt.end_datetime

            # Ensure we don't set future datetimes
            if prescription.created_datetime > current:
                prescription.created_datetime = current

            session.add(prescription)
            session.flush()

            # Add prescription items (select unique medications)
            selected_medications = fake.random_elements(
                elements=medications, length=num_medications, unique=True
            )

            for medication in selected_medications:
                item = PrescriptionItem(
                    prescription_id=prescription.prescription_id,
                    medication_id=medication.medication_id,
                    instructions=fake.sentence(nb_words=12, variable_nb_words=True),
                )
                session.add(item)

        elif outcome == "cancelled":
            # Determine who cancels: 70% patient, 30% doctor
            canceller = fake.random_element(
                OrderedDict([("patient", 70), ("doctor", 30)])
            )

            if canceller == "patient":
                cancelled_by_profile_id = appt.patient_profile_id
            else:
                cancelled_by_profile_id = appt.doctor_profile_id

            cancellation_reason = fake.sentence(nb_words=15, variable_nb_words=True)

            # Set cancellation datetime
            # Should be: after appointment creation, before appointment start, within cancellation window
            days_until_appointment = (appt.start_datetime - current).days

            if days_until_appointment > 0:
                # Appointment in future - cancelled sometime between creation and now
                earliest_cancel = appt.created_datetime
                latest_cancel = min(
                    current,
                    appt.start_datetime - timedelta(hours=1),  # At least 1 hour before
                )

                if latest_cancel > earliest_cancel:
                    total_seconds = int(
                        (latest_cancel - earliest_cancel).total_seconds()
                    )
                    offset = fake.random_int(0, total_seconds)
                    cancelled_datetime = earliest_cancel + timedelta(seconds=offset)
                else:
                    cancelled_datetime = earliest_cancel
            else:
                # Appointment already passed - this shouldn't happen for cancellation
                # but handle edge case
                cancelled_datetime = appt.created_datetime

            # Ensure no future datetime
            if cancelled_datetime > current:
                cancelled_datetime = current

            # Store the cancellation datetime before calling cancel()
            # since cancel() will set it to datetime.now()
            target_cancelled_datetime = cancelled_datetime

            appt.cancel(
                cancelled_by_profile_id=cancelled_by_profile_id,
                cancellation_reason=cancellation_reason,
            )

            # Override the cancelled_datetime set by cancel() method
            appt.cancelled_datetime = target_cancelled_datetime

        elif outcome == "missed":
            # Mark as missed (patient no-show)
            appt.miss()

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
