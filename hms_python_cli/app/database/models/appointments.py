from typing import TYPE_CHECKING, Optional, List
from datetime import datetime
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    Index,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

from app.lookups.enums import AppointmentRequestStatusEnum, AppointmentStatusEnum

if TYPE_CHECKING:
    from .profiles import PatientProfile, DoctorProfile, Profile
    from .specialty import Specialty
    from .prescription import Prescription


class AppointmentRequestStatus(Base):
    """Appointment request status lookup table"""

    __tablename__ = "appointment_request_status"

    appointment_request_status_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(50))

    # Relationships
    appointment_requests: Mapped[List["AppointmentRequest"]] = relationship(
        "AppointmentRequest", back_populates="status"
    )


class AppointmentRequest(Base):
    """Appointment request - patients request appointments"""

    __tablename__ = "appointment_request"
    __table_args__ = (
        Index(
            "idx_request_status_created",
            "appointment_request_status_id",
            "created_datetime",
        ),
    )

    appointment_request_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    patient_profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patient_profile.profile_id")
    )
    specialty_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("specialty.specialty_id")
    )
    reason: Mapped[str] = mapped_column(Text)
    preferred_doctor_profile_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("doctor_profile.profile_id")
    )
    preferred_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_datetime: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    appointment_request_status_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("appointment_request_status.appointment_request_status_id")
    )
    appointment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("appointment.appointment_id")
    )

    handled_by_profile_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("profile.profile_id")
    )
    handled_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    handling_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    patient: Mapped["PatientProfile"] = relationship(
        "PatientProfile", back_populates="appointment_requests"
    )
    specialty: Mapped["Specialty"] = relationship(
        "Specialty",
        back_populates="appointment_requests",
    )
    preferred_doctor: Mapped[Optional["DoctorProfile"]] = relationship(
        "DoctorProfile", back_populates="preferred_appointment_requests"
    )
    status: Mapped["AppointmentRequestStatus"] = relationship(
        "AppointmentRequestStatus", back_populates="appointment_requests"
    )
    appointment: Mapped[Optional["Appointment"]] = relationship(
        "Appointment",
        foreign_keys=[appointment_id],
        back_populates="appointment_requests",
    )
    handled_by: Mapped[Optional["Profile"]] = relationship(
        "Profile", back_populates="handled_appointment_requests"
    )

    @property
    def status_enum(self):
        return AppointmentRequestStatusEnum(self.appointment_request_status_id)

    @property
    def is_pending(self):
        return (
            self.appointment_request_status_id == AppointmentRequestStatusEnum.PENDING
        )

    @property
    def is_approved(self):
        return (
            self.appointment_request_status_id == AppointmentRequestStatusEnum.APPROVED
        )

    @property
    def is_cancelled(self):
        return (
            self.appointment_request_status_id == AppointmentRequestStatusEnum.CANCELLED
        )

    @property
    def is_rejected(self):
        return (
            self.appointment_request_status_id == AppointmentRequestStatusEnum.REJECTED
        )

    def approve(
        self,
        appointment_id: int,
        handled_by_profile_id: int,
        handling_notes: str | None,
    ):
        if self.status_enum != AppointmentRequestStatusEnum.PENDING:
            raise ValueError("Only pending appointment requests can be approved.")
        self.appointment_request_status_id = AppointmentRequestStatusEnum.APPROVED
        self.appointment_id = appointment_id
        self.handled_by_profile_id = handled_by_profile_id
        self.handling_notes = handling_notes
        self.handled_datetime = datetime.now()

    def cancel(
        self,
    ):
        if self.status_enum != AppointmentRequestStatusEnum.PENDING:
            raise ValueError("Only pending appointment requests can be cancelled.")
        self.appointment_request_status_id = AppointmentRequestStatusEnum.CANCELLED
        self.handled_datetime = datetime.now()

    def reject(self, handled_by_profile_id: int, handling_notes: str):
        if self.status_enum != AppointmentRequestStatusEnum.PENDING:
            raise ValueError("Only pending appointment requests can be rejected.")
        self.appointment_request_status_id = AppointmentRequestStatusEnum.REJECTED
        self.handled_by_profile_id = handled_by_profile_id
        self.handling_notes = handling_notes
        self.handled_datetime = datetime.now()


class AppointmentStatus(Base):
    """Appointment status lookup table"""

    __tablename__ = "appointment_status"

    appointment_status_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(50))

    # Relationships
    appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment", back_populates="status"
    )


class Appointment(Base):
    """Appointment - scheduled patient-doctor appointments"""

    __tablename__ = "appointment"
    __table_args__ = (
        Index("idx_patient_start", "patient_profile_id", "start_datetime"),
        Index("idx_doctor_start", "doctor_profile_id", "start_datetime"),
        CheckConstraint("start_datetime < end_datetime", name="check_datetime_order"),
    )

    appointment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    start_datetime: Mapped[datetime] = mapped_column(DateTime)
    end_datetime: Mapped[datetime] = mapped_column(DateTime)
    patient_profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patient_profile.profile_id")
    )
    doctor_profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctor_profile.profile_id")
    )
    specialty_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("specialty.specialty_id")
    )
    room_name: Mapped[str] = mapped_column(String(50))
    reason: Mapped[str] = mapped_column(Text)
    appointment_status_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("appointment_status.appointment_status_id")
    )

    created_by_profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("profile.profile_id")
    )
    created_datetime: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    cancelled_by_profile_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("profile.profile_id")
    )
    cancelled_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    patient: Mapped["PatientProfile"] = relationship(
        "PatientProfile",
        foreign_keys=[patient_profile_id],
        back_populates="appointments",
    )
    doctor: Mapped["DoctorProfile"] = relationship(
        "DoctorProfile", foreign_keys=[doctor_profile_id], back_populates="appointments"
    )
    specialty: Mapped["Specialty"] = relationship(
        "Specialty", back_populates="appointments"
    )
    status: Mapped["AppointmentStatus"] = relationship(
        "AppointmentStatus", back_populates="appointments"
    )

    created_by: Mapped["Profile"] = relationship(
        "Profile",
        foreign_keys=[created_by_profile_id],
        back_populates="created_appointments",
    )
    cancelled_by: Mapped[Optional["Profile"]] = relationship(
        "Profile",
        foreign_keys=[cancelled_by_profile_id],
        back_populates="cancelled_appointments",
    )

    prescriptions: Mapped[List["Prescription"]] = relationship(
        "Prescription", back_populates="appointment"
    )
    appointment_requests: Mapped[List["AppointmentRequest"]] = relationship(
        "AppointmentRequest",
        foreign_keys="AppointmentRequest.appointment_id",
        back_populates="appointment",
    )

    @property
    def status_enum(self):
        return AppointmentStatusEnum(self.appointment_status_id)

    @property
    def is_scheduled(self):
        return self.appointment_status_id == AppointmentStatusEnum.SCHEDULED

    @property
    def is_completed(self):
        return self.appointment_status_id == AppointmentStatusEnum.COMPLETED

    @property
    def is_cancelled(self):
        return self.appointment_status_id == AppointmentStatusEnum.CANCELLED

    @property
    def is_missed(self):
        return self.appointment_status_id == AppointmentStatusEnum.MISSED

    def complete(self):
        if self.status != AppointmentStatusEnum.SCHEDULED:
            raise ValueError("Only scheduled appointments can be completed.")
        self.appointment_status_id = AppointmentStatusEnum.COMPLETED

    def cancel(self, cancelled_by_profile_id: int, cancellation_reason: str):
        if self.status != AppointmentStatusEnum.SCHEDULED:
            raise ValueError("Only scheduled appointments can be cancelled.")
        self.appointment_status_id = AppointmentStatusEnum.CANCELLED
        self.cancelled_by_profile_id = cancelled_by_profile_id
        self.cancellation_reason = cancellation_reason

    def miss(self):
        if self.status != AppointmentStatusEnum.SCHEDULED:
            raise ValueError("Only scheduled appointments can be missed.")
        self.appointment_status_id = AppointmentStatusEnum.MISSED
