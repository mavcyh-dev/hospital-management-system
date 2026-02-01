from typing import Sequence

from app.database.models import Appointment, AppointmentRequest
from rich.console import Console
from rich.table import Table
from rich.text import Text


def receptionist_display_appointment_requests_table(
    console: Console,
    appointment_requests: Sequence[AppointmentRequest] | AppointmentRequest,
    *,
    title="Appointment Requests",
    max_count: int | None = None,
    start_index: int | None = None,
):
    display_one = isinstance(appointment_requests, AppointmentRequest)
    display_list = (
        not isinstance(appointment_requests, AppointmentRequest)
        and max_count is not None
        and start_index is None
    )
    display_scrolling = (
        not isinstance(appointment_requests, AppointmentRequest)
        and max_count is not None
        and start_index is not None
    )
    if not (display_one or display_list or display_scrolling):
        raise ValueError("Can only either display one, a list or scrolling list.")

    if display_list:
        assert max_count is not None
        assert not isinstance(appointment_requests, AppointmentRequest)
        if len(appointment_requests) > max_count:
            title += f" ({max_count}/{len(appointment_requests)})"
        else:
            title += f" ({len(appointment_requests)})"
    elif display_scrolling:
        assert max_count is not None
        assert start_index is not None
        assert not isinstance(appointment_requests, AppointmentRequest)
        title += f" ({start_index+1}-{min(start_index+max_count, len(appointment_requests))}/{len(appointment_requests)})"

    table = Table(title=title, title_justify="left", show_lines=True)
    if display_scrolling:
        table.add_column("No.")
    table.add_column("Status")
    table.add_column("Created by")
    table.add_column("Created on")
    table.add_column("Specialty")
    table.add_column("Reason")
    table.add_column("Preferred Doctor")
    table.add_column("Preferred Datetime")

    start_index = start_index if start_index else 0
    max_count = max_count if max_count else 1
    if display_one:
        appointment_requests = (appointment_requests,)
    for offset, appointment_request in enumerate(
        appointment_requests[start_index : start_index + max_count]
    ):
        row = [
            appointment_request.status_enum.display,
            appointment_request.patient.full_name,
            appointment_request.created_datetime.strftime("%Y-%m-%d"),
            appointment_request.specialty.name,
            appointment_request.reason,
            (
                appointment_request.preferred_doctor.full_name
                if appointment_request.preferred_doctor
                else Text("[empty]", style="italic dim")
            ),
            (
                appointment_request.preferred_datetime.strftime("%Y-%m-%d %H:%M")
                if appointment_request.preferred_datetime
                else Text("[empty]", style="italic dim")
            ),
        ]
        if display_scrolling:
            assert start_index is not None
            row.insert(0, str(start_index + offset + 1))
        table.add_row(*row)
    console.print(table)
    console.print("")

    if display_one:
        (appointment_request,) = appointment_requests
        if appointment_request.is_rejected:
            table = Table(title="Rejection Details", title_justify="left")
            table.add_column("On Datetime")
            table.add_column("By")
            table.add_column("Reason")

            assert appointment_request.handled_datetime is not None
            assert appointment_request.handled_by is not None
            assert appointment_request.handling_notes is not None
            table.add_row(
                appointment_request.handled_datetime.strftime("%Y-%m-%d %H:%M"),
                appointment_request.handled_by.type_enum.display,
                appointment_request.handling_notes,
            )
            console.print(table)
            console.print("")


def receptionist_display_appointments_table(
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
    table.add_column("Created on")
    table.add_column("Start")
    table.add_column("End")
    table.add_column("Room")
    table.add_column("Specialty")
    table.add_column("Reason")
    table.add_column("Doctor")

    start_index = start_index if start_index else 0
    max_count = max_count if max_count else 1
    if display_one:
        appointments = (appointments,)
    for offset, appointment in enumerate(
        appointments[start_index : start_index + max_count]
    ):
        row = [
            appointment.status_enum.display,
            appointment.created_datetime.strftime("%Y-%m-%d"),
            appointment.start_datetime.strftime("%Y-%m-%d %H:%M"),
            appointment.end_datetime.strftime("%Y-%m-%d %H:%M"),
            appointment.room_name,
            appointment.specialty.name,
            appointment.reason,
            appointment.doctor.full_name,
        ]
        if display_scrolling:
            assert start_index is not None
            row.insert(0, str(start_index + offset + 1))
        table.add_row(*row)
    console.print(table)
    console.print("")

    if display_one:
        (appointment,) = appointments
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
