from enum import IntEnum


class BaseEnum(IntEnum):
    @property
    def display(self) -> str:
        return self.name.replace("_", " ").title()


class SexEnum(BaseEnum):
    UNKNOWN = 0
    MALE = 1
    FEMALE = 2
    NOT_APPLICABLE = 9


class ProfileTypeEnum(BaseEnum):
    PATIENT = 1
    DOCTOR = 2
    RECEPTIONIST = 3
    ADMIN = 4


class AppointmentRequestStatusEnum(BaseEnum):
    PENDING = 1
    APPROVED = 2
    CANCELLED = 3
    REJECTED = 4


class AppointmentStatusEnum(BaseEnum):
    SCHEDULED = 1
    COMPLETED = 2
    CANCELLED = 3
    MISSED = 4
