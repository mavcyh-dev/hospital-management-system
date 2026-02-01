from typing import TYPE_CHECKING, List
from sqlalchemy import String, Integer, Boolean, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .profiles import DoctorProfile
    from .appointments import Appointment, AppointmentRequest


# Association table for doctor-specialty many-to-many relationship
doctor_specialty = Table(
    "doctor_specialty",
    Base.metadata,
    Column(
        "doctor_profile_id",
        Integer,
        ForeignKey("doctor_profile.profile_id"),
        primary_key=True,
    ),
    Column(
        "specialty_id", Integer, ForeignKey("specialty.specialty_id"), primary_key=True
    ),
)


class Specialty(Base):
    """Medical specialties (e.g., Cardiology, Pediatrics)"""

    __tablename__ = "specialty"

    specialty_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(100))
    is_in_service: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    doctors: Mapped[List["DoctorProfile"]] = relationship(
        "DoctorProfile", secondary=doctor_specialty, back_populates="specialties"
    )
    appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment", back_populates="specialty"
    )
    appointment_requests: Mapped[List["AppointmentRequest"]] = relationship(
        "AppointmentRequest", back_populates="specialty"
    )
