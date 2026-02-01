from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .appointments import Appointment
    from .profiles import DoctorProfile, PatientProfile


class Prescription(Base):
    """Prescription - doctor prescribes medications to patient"""

    __tablename__ = "prescription"
    __table_args__ = (
        Index("idx_patient_created", "patient_profile_id", "created_datetime"),
    )

    prescription_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    patient_profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patient_profile.profile_id")
    )
    doctor_profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctor_profile.profile_id")
    )
    appointment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("appointment.appointment_id")
    )
    created_datetime: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    patient: Mapped["PatientProfile"] = relationship(
        "PatientProfile", back_populates="prescriptions"
    )
    doctor: Mapped["DoctorProfile"] = relationship(
        "DoctorProfile", back_populates="prescriptions"
    )
    appointment: Mapped[Optional["Appointment"]] = relationship(
        "Appointment", back_populates="prescriptions"
    )
    items: Mapped[List["PrescriptionItem"]] = relationship(
        "PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan"
    )


class PrescriptionItem(Base):
    """Individual medications within a prescription"""

    __tablename__ = "prescription_item"
    __table_args__ = (Index("idx_prescription_id", "prescription_id"),)

    prescription_item_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    prescription_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("prescription.prescription_id")
    )
    medication_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("medication.medication_id")
    )
    instructions: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    prescription: Mapped["Prescription"] = relationship(
        "Prescription", back_populates="items"
    )
    medication: Mapped["Medication"] = relationship(
        "Medication", back_populates="prescription_items"
    )


class Medication(Base):
    """Medication catalog - available medications"""

    __tablename__ = "medication"

    medication_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    generic_name: Mapped[str] = mapped_column(Text)
    is_in_service: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    prescription_items: Mapped[List["PrescriptionItem"]] = relationship(
        "PrescriptionItem", back_populates="medication"
    )
