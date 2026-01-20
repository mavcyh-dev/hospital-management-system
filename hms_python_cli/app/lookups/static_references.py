from app.database.models.profiles import ProfileType
from app.database.models.appointments import AppointmentRequestStatus, AppointmentStatus
from app.lookups.enums import (
    ProfileTypeEnum,
    AppointmentRequestStatusEnum,
    AppointmentStatusEnum,
)

PROFILE_TYPE_ENUM_TO_NAME = {
    ProfileTypeEnum.PATIENT: "PATIENT",
    ProfileTypeEnum.DOCTOR: "DOCTOR",
    ProfileTypeEnum.RECEPTIONIST: "RECEPTIONIST",
    ProfileTypeEnum.ADMIN: "ADMIN"
}

PROFILE_TYPES = [
    ProfileType(profile_type_id=ProfileTypeEnum.PATIENT, name="PATIENT"),
    ProfileType(profile_type_id=ProfileTypeEnum.DOCTOR, name="DOCTOR"),
    ProfileType(profile_type_id=ProfileTypeEnum.RECEPTIONIST, name="RECEPTIONIST"),
    ProfileType(profile_type_id=ProfileTypeEnum.ADMIN, name="ADMIN"),
]

APPOINTMENT_REQUEST_STATUSES = [
    AppointmentRequestStatus(
        appointment_request_status_id=AppointmentRequestStatusEnum.PENDING,
        name="PENDING",
    ),
    AppointmentRequestStatus(
        appointment_request_status_id=AppointmentRequestStatusEnum.APPROVED,
        name="APPROVED",
    ),
    AppointmentRequestStatus(
        appointment_request_status_id=AppointmentRequestStatusEnum.REJECTED,
        name="REJECTED",
    ),
]

APPOINTMENT_STATUSES = [
    AppointmentStatus(
        appointment_status_id=AppointmentStatusEnum.SCHEDULED, name="SCHEDULED"
    ),
    AppointmentStatus(
        appointment_status_id=AppointmentStatusEnum.COMPLETED, name="COMPLETED"
    ),
    AppointmentStatus(
        appointment_status_id=AppointmentStatusEnum.CANCELLED, name="CANCELLED"
    ),
]
