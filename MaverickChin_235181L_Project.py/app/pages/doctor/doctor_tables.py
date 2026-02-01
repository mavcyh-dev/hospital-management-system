from datetime import date
from typing import Sequence

from app.database.models import Appointment, Prescription
from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def doctor_display_appointments_table(
    console: Console,
    appointments: Sequence[Appointment] | Appointment,
    *,
    title: str = "Appointments",
    max_count: int | None = None,
    start_index: int | None = None,
):
    display_one = isinstance(appointments, Appointment)
    display_list = (
        not isinstance(appointments, Appointment)
        and max_count is not None
        and start_index is None
    )
    display_scrolling = (
        not isinstance(appointments, Appointment)
        and max_count is not None
        and start_index is not None
    )
    if not (display_one or display_list or display_scrolling):
        raise ValueError("Can only either display one, a list or scrolling list.")

    if display_list:
        assert max_count is not None
        assert not isinstance(appointments, Appointment)
        if len(appointments) > max_count:
            title += f" ({max_count}/{len(appointments)})"
        else:
            title += f" ({len(appointments)})"
    elif display_scrolling:
        assert max_count is not None
        assert start_index is not None
        assert not isinstance(appointments, Appointment)
        title += f" ({start_index+1}-{min(start_index+max_count, len(appointments))}/{len(appointments)})"

    table = Table(title=title, title_justify="left", show_lines=True)
    if display_scrolling:
        table.add_column("No.")
    table.add_column("Status")
    table.add_column("Created by")
    table.add_column("Created on")
    table.add_column("Start")
    table.add_column("End")
    table.add_column("Room")
    table.add_column("Specialty")
    table.add_column("Reason")
    if not display_one:
        table.add_column("Patient")

    start_index = start_index if start_index else 0
    max_count = max_count if max_count else 1
    if display_one:
        appointments = (appointments,)
    for offset, appointment in enumerate(
        appointments[start_index : start_index + max_count]
    ):
        row: list[RenderableType] = [
            appointment.status_enum.display,
            appointment.created_by.type_enum.display,
            appointment.created_datetime.strftime("%Y-%m-%d"),
            appointment.start_datetime.strftime("%Y-%m-%d %H:%M"),
            appointment.end_datetime.strftime("%Y-%m-%d %H:%M"),
            appointment.room_name,
            appointment.specialty.name,
            appointment.reason,
        ]
        if not display_one:
            row.append(appointment.patient.full_name)
        if display_scrolling:
            assert start_index is not None
            row.insert(0, str(start_index + offset + 1))
        table.add_row(*row)
    console.print(table)
    console.print("")

    # Display doctor's notes and patient details
    if display_one:
        (appointment,) = appointments
        if appointment.doctor_notes:
            console.print(
                Panel(
                    appointment.doctor_notes,
                    title="Doctor's notes",
                    title_align="left",
                    padding=(1, 1),
                )
            )
            console.print("")
        else:
            console.print(Panel("No doctor's notes found."))
            console.print("")

        table = Table(title="Patient Details", title_justify="left")
        table.add_column("Name")
        table.add_column("Sex")
        table.add_column("Date of Birth / Age")
        table.add_column("Medication Allergies")
        table.add_column("Phone Number")
        table.add_column("Email")

        patient = appointment.patient
        person = patient.profile.person

        today = date.today()
        birth = person.date_of_birth
        age = today.year - birth.year
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1
        table.add_row(
            patient.full_name,
            person.sex_enum.display,
            f"{person.date_of_birth.strftime("%Y-%m-%d")} / {age}",
            (
                appointment.patient.medication_allergies
                if appointment.patient.medication_allergies
                else Text("[empty]", style="italic dim")
            ),
            person.primary_phone_number,
            person.primary_email,
        )
        console.print(table)
        console.print("")

        if appointment.is_cancelled:
            table = Table(title="Cancellation Details", title_justify="left")
            table.add_column("On")
            table.add_column("By")
            table.add_column("Reason")

            assert appointment.cancelled_datetime is not None
            assert appointment.cancelled_by is not None
            assert appointment.cancellation_reason is not None
            table.add_row(
                appointment.cancelled_datetime.strftime("%Y-%m-%d %H:%M"),
                appointment.cancelled_by.type_enum.display,
                appointment.cancellation_reason,
            )
            console.print(table)
            console.print("")

        if appointment.prescriptions:
            doctor_display_prescription_items_for_prescriptions_table(
                console, appointment.prescriptions
            )
        else:
            console.print(Panel("No prescriptions found."))
            console.print("")


def doctor_display_prescription_items_for_prescriptions_table(
    console: Console,
    prescriptions: Sequence[Prescription],
    *,
    title: str = "Prescription",
    show_number: bool = True,
):
    for prescription in prescriptions:
        title += (
            f" (Created on {prescription.created_datetime.strftime("%Y-%m-%d %H:%M")})"
        )
        table = Table(title=title, title_justify="left", show_lines=True)
        if show_number:
            table.add_column("No.")
        table.add_column("Medication (Generic Name)")
        table.add_column("Instructions")

        for idx, item in enumerate(prescription.items):
            row: list[RenderableType] = [
                item.medication.generic_name,
                (
                    item.instructions
                    if item.instructions
                    else Text("[empty]", style="italic dim")
                ),
            ]
            if show_number:
                row.insert(0, str(idx + 1))
            table.add_row(*row)
        console.print(table)
        console.print("")
