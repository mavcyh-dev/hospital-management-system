from app.database.models import (
    AdminProfile,
    DoctorProfile,
    PatientProfile,
    ReceptionistProfile,
    User,
)
from rich.console import Console
from rich.table import Table
from rich.text import Text


def admin_display_user_details_table(
    console: Console,
    user: User,
):
    table = Table(title="User details", title_justify="left")
    table.add_column("Username")
    table.add_column("Created on")
    table.add_column("Status")
    table.add_row(
        user.username,
        user.created_datetime.strftime("%Y-%m-%d %H:%M"),
        "In service" if user.is_in_service else "Deactivated",
    )
    console.print(table)
    console.print("")

    person = user.person
    table = Table(title="Person details", title_justify="left")
    table.add_column("First Name")
    table.add_column("Last Name")
    table.add_column("Sex")
    table.add_column("Date of Birth")
    table.add_column("Email")
    table.add_column("Phone Number")
    table.add_column("Home Address")
    table.add_row(
        person.first_name,
        person.last_name,
        person.sex_enum.display,
        person.date_of_birth.strftime("%Y-%m-%d"),
        person.primary_email,
        person.primary_phone_number,
        person.primary_home_address,
    )
    console.print(table)
    console.print("")


def admin_display_patient_profile_details_table(
    console: Console, patient_profile: PatientProfile
):
    table = Table(title="Patient profile metadata", title_justify="left")
    table.add_column("Status")
    table.add_column("Created on")
    table.add_row(
        "In service" if patient_profile.profile.is_in_service else "Deactivated",
        patient_profile.profile.created_datetime.strftime("%Y-%m-%d %H:%M"),
    )
    console.print(table)
    console.print("")

    table = Table(title="Patient profile information", title_justify="left")
    table.add_column("Medication allergies")
    table.add_row(
        (
            patient_profile.medication_allergies
            if patient_profile.medication_allergies
            else Text("[empty]", style="italic dim")
        ),
    )
    console.print(table)
    console.print("")

    requests = patient_profile.appointment_requests
    total_count = len(requests)
    pending_count = sum(1 for x in requests if x.is_pending)
    approved_count = sum(1 for x in requests if x.is_approved)
    rejected_count = sum(1 for x in requests if x.is_rejected)
    cancelled_count = sum(1 for x in requests if x.is_cancelled)

    table = Table(title="Appointment requests", title_justify="left")
    table.add_column("Created")
    table.add_column("Pending")
    table.add_column("Approved")
    table.add_column("Rejected")
    table.add_column("Cancelled")
    table.add_row(
        str(total_count),
        str(pending_count),
        str(approved_count),
        str(rejected_count),
        str(cancelled_count),
    )
    console.print(table)
    console.print("")

    appts = patient_profile.appointments
    total_count = len(appts)
    scheduled_count = sum(1 for x in appts if x.is_scheduled)
    completed_count = sum(1 for x in appts if x.is_completed)
    cancelled_count = sum(1 for x in appts if x.is_cancelled)
    missed_count = sum(1 for x in appts if x.is_missed)
    table = Table(title="Appointments", title_justify="left")
    table.add_column("Total")
    table.add_column("Scheduled")
    table.add_column("Completed")
    table.add_column("Cancelled")
    table.add_column("Missed")
    table.add_row(
        str(total_count),
        str(scheduled_count),
        str(completed_count),
        str(cancelled_count),
        str(missed_count),
    )
    console.print(table)
    console.print("")


def admin_display_doctor_profile_details_table(
    console: Console, doctor_profile: DoctorProfile
):
    table = Table(title="Doctor profile metadata", title_justify="left")
    table.add_column("Status")
    table.add_column("Created on")
    table.add_row(
        "In service" if doctor_profile.profile.is_in_service else "Deactivated",
        doctor_profile.profile.created_datetime.strftime("%Y-%m-%d %H:%M"),
    )
    console.print(table)
    console.print("")

    table = Table(title="Doctor profile information", title_justify="left")
    table.add_column("Office Phone Number")
    table.add_column("Specialties")
    table.add_row(
        (
            doctor_profile.office_phone_number
            if doctor_profile.office_phone_number
            else Text("[empty]", style="italic dim")
        ),
        ", ".join(s.name for s in doctor_profile.specialties),
    )
    console.print(table)
    console.print("")

    appts = doctor_profile.appointments
    total_count = len(appts)
    scheduled_count = sum(1 for x in appts if x.is_scheduled)
    completed_count = sum(1 for x in appts if x.is_completed)
    cancelled_count = sum(1 for x in appts if x.is_cancelled)
    missed_count = sum(1 for x in appts if x.is_missed)
    table = Table(title="Appointments", title_justify="left")
    table.add_column("Total")
    table.add_column("Scheduled")
    table.add_column("Completed")
    table.add_column("Cancelled")
    table.add_column("Missed")
    table.add_row(
        str(total_count),
        str(scheduled_count),
        str(completed_count),
        str(cancelled_count),
        str(missed_count),
    )
    console.print(table)
    console.print("")


def admin_display_receptionist_profile_metadata_table(
    console: Console, receptionist_profile: ReceptionistProfile
):
    table = Table(title="Receptionist profile metadata", title_justify="left")
    table.add_column("Status")
    table.add_column("Created on")
    table.add_row(
        "In service" if receptionist_profile.profile.is_in_service else "Deactivated",
        receptionist_profile.profile.created_datetime.strftime("%Y-%m-%d %H:%M"),
    )
    console.print(table)
    console.print("")


def admin_display_admin_profile_metadata_table(
    console: Console, admin_profile: AdminProfile
):
    table = Table(title="Admin profile metadata", title_justify="left")
    table.add_column("Status")
    table.add_column("Created on")
    table.add_row(
        "In service" if admin_profile.profile.is_in_service else "Deactivated",
        admin_profile.profile.created_datetime.strftime("%Y-%m-%d %H:%M"),
    )
    console.print(table)
    console.print("")
