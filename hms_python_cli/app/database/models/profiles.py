from typing import TYPE_CHECKING, Optional, List
from datetime import datetime
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    Boolean,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .user_person import Person
    from .specialty import Specialty
    from .appointments import Appointment, AppointmentRequest
    from .prescription import Prescription


class ProfileType(Base):
    """Profile type lookup table (doctor, patient, receptionist, admin)"""

    __tablename__ = "profile_type"

    profile_type_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(32), unique=True)

    # Relationships
    profiles: Mapped[List["Profile"]] = relationship(
        "Profile", back_populates="profile_type"
    )


class Profile(Base):
    """Profile - links Person to profile types with role-specific details"""

    __tablename__ = "profile"
    __table_args__ = (
        UniqueConstraint("person_id", "profile_type_id", name="uq_person_profile_type"),
    )

    profile_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("person.person_id"))
    profile_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("profile_type.profile_type_id")
    )
    created_datetime: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    is_in_service: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    person: Mapped["Person"] = relationship("Person", back_populates="profiles")
    profile_type: Mapped["ProfileType"] = relationship(
        "ProfileType", back_populates="profiles"
    )

    # Role-specific profile relationships (one-to-one)
    doctor_profile: Mapped[Optional["DoctorProfile"]] = relationship(
        "DoctorProfile", back_populates="profile", uselist=False
    )
    patient_profile: Mapped[Optional["PatientProfile"]] = relationship(
        "PatientProfile", back_populates="profile", uselist=False
    )
    receptionist_profile: Mapped[Optional["ReceptionistProfile"]] = relationship(
        "ReceptionistProfile", back_populates="profile", uselist=False
    )
    admin_profile: Mapped[Optional["AdminProfile"]] = relationship(
        "AdminProfile", back_populates="profile", uselist=False
    )

    # Appointments created by this profile
    created_appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment",
        foreign_keys="Appointment.created_by_profile_id",
        back_populates="created_by",
    )
    cancelled_appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment",
        foreign_keys="Appointment.cancelled_by_profile_id",
        back_populates="cancelled_by",
    )
    handled_appointment_requests: Mapped[List["AppointmentRequest"]] = relationship(
        "AppointmentRequest", back_populates="handled_by"
    )


class DoctorProfile(Base):
    """Doctor-specific profile details"""

    __tablename__ = "doctor_profile"

    profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("profile.profile_id"), primary_key=True
    )
    office_phone_number: Mapped[Optional[str]] = mapped_column(String(32))

    # Relationships
    profile: Mapped["Profile"] = relationship(
        "Profile", back_populates="doctor_profile"
    )
    specialties: Mapped[List["Specialty"]] = relationship(
        "Specialty", secondary="doctor_specialty", back_populates="doctors"
    )
    appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment",
        foreign_keys="Appointment.doctor_profile_id",
        back_populates="doctor",
    )
    prescriptions: Mapped[List["Prescription"]] = relationship(
        "Prescription", back_populates="doctor"
    )
    preferred_appointment_requests: Mapped[List["AppointmentRequest"]] = relationship(
        "AppointmentRequest", back_populates="preferred_doctor"
    )

    @property
    def full_name(self):
        return f"{self.profile.person.full_name}"


class PatientProfile(Base):
    """Patient-specific profile details"""

    __tablename__ = "patient_profile"

    profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("profile.profile_id"), primary_key=True
    )
    medication_allergies: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    profile: Mapped["Profile"] = relationship(
        "Profile", back_populates="patient_profile"
    )
    appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment",
        foreign_keys="Appointment.patient_profile_id",
        back_populates="patient",
    )
    prescriptions: Mapped[List["Prescription"]] = relationship(
        "Prescription", back_populates="patient"
    )
    appointment_requests: Mapped[List["AppointmentRequest"]] = relationship(
        "AppointmentRequest", back_populates="patient"
    )

    @property
    def full_name(self):
        return f"{self.profile.person.full_name}"


class ReceptionistProfile(Base):
    """Receptionist-specific profile details"""

    __tablename__ = "receptionist_profile"

    profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("profile.profile_id"), primary_key=True
    )

    # Relationships
    profile: Mapped["Profile"] = relationship(
        "Profile", back_populates="receptionist_profile"
    )

    @property
    def full_name(self):
        return f"{self.profile.person.full_name}"


class AdminProfile(Base):
    """Admin-specific profile details"""

    __tablename__ = "admin_profile"

    profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("profile.profile_id"), primary_key=True
    )

    # Relationships
    profile: Mapped["Profile"] = relationship("Profile", back_populates="admin_profile")

    @property
    def full_name(self):
        return f"{self.profile.person.full_name}"
