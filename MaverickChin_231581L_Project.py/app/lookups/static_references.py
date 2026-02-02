from app.database.models.profiles import ProfileType
from app.database.models.appointments import AppointmentRequestStatus, AppointmentStatus
from app.lookups.enums import (
    ProfileTypeEnum,
    AppointmentRequestStatusEnum,
    AppointmentStatusEnum,
)

PROFILE_TYPES = [
    ProfileType(profile_type_id=enum, name=enum.display.capitalize())
    for enum in ProfileTypeEnum
]


APPOINTMENT_REQUEST_STATUSES = [
    AppointmentRequestStatus(
        appointment_request_status_id=enum, name=enum.display.capitalize()
    )
    for enum in AppointmentRequestStatusEnum
]

APPOINTMENT_STATUSES = [
    AppointmentStatus(appointment_status_id=enum, name=enum.display.capitalize())
    for enum in AppointmentStatusEnum
]
