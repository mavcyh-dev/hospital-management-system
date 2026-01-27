from datetime import datetime
from typing import Sequence

from app.database.models import (
    Appointment,
    DoctorProfile,
    PatientProfile,
    Prescription,
    PrescriptionItem,
    Profile,
)
from sqlalchemy import Row, select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.interfaces import LoaderOption

from .base_repository import BaseRepository


class AppointmentLoad:
    SPECIALTY = joinedload(Appointment.specialty)
    DOCTOR_WITH_PERSON = (
        joinedload(Appointment.doctor)
        .joinedload(DoctorProfile.profile)
        .joinedload(Profile.person)
    )
    PATIENT_WITH_PERSON = (
        joinedload(Appointment.patient)
        .joinedload(PatientProfile.profile)
        .joinedload(Profile.person)
    )
    CREATED_BY_PROFILE = joinedload(Appointment.created_by)
    CANCELLED_BY_PROFILE = joinedload(Appointment.cancelled_by)
    PRESCRIPTION_WITH_ITEMS_WITH_MEDICATION = (
        joinedload(Appointment.prescriptions)
        .joinedload(Prescription.items)
        .joinedload(PrescriptionItem.medication)
    )


class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self):
        super().__init__(Appointment)

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------
    def list_by_patient_profile_id(
        self,
        session: Session,
        patient_profile_id: int,
        *,
        only_include_status_ids: Sequence[int] | None = None,
        datetime_range: tuple[datetime, datetime] | None = None,
        order_by_created_datetime_desc: bool | None = None,
        loaders: Sequence[LoaderOption] = (),
    ) -> Sequence[Appointment]:
        stmt = (
            select(Appointment)
            .where(Appointment.patient_profile_id == patient_profile_id)
            .options(*loaders)
        )

        if only_include_status_ids:
            stmt = stmt.where(
                Appointment.appointment_status_id.in_(only_include_status_ids)
            )
        if datetime_range:
            start, end = datetime_range
            stmt = stmt.where(
                Appointment.start_datetime >= start,
                Appointment.end_datetime <= end,
            )
        if order_by_created_datetime_desc is not None:
            stmt = stmt.order_by(
                Appointment.created_datetime.desc()
                if order_by_created_datetime_desc
                else Appointment.created_datetime.asc()
            )
        return session.scalars(stmt).all()

    def list_by_doctor_profile_id(
        self,
        session: Session,
        doctor_profile_id: int,
        *,
        only_include_status_ids: Sequence[int] | None = None,
        datetime_range: tuple[datetime, datetime] | None = None,
        order_by_created_datetime_desc: bool | None = None,
        loaders: Sequence[LoaderOption] = (),
    ) -> Sequence[Appointment]:
        stmt = (
            select(Appointment)
            .where(Appointment.doctor_profile_id == doctor_profile_id)
            .options(*loaders)
        )

        if only_include_status_ids:
            stmt = stmt.where(
                Appointment.appointment_status_id.in_(only_include_status_ids)
            )
        if datetime_range:
            start, end = datetime_range
            stmt = stmt.where(
                Appointment.start_datetime >= start,
                Appointment.end_datetime <= end,
            )
        if order_by_created_datetime_desc is not None:
            stmt = stmt.order_by(
                Appointment.created_datetime.desc()
                if order_by_created_datetime_desc
                else Appointment.created_datetime.asc()
            )
        return session.scalars(stmt).all()

    def list_appointment_details_by_doctor_profile_id(
        self,
        session: Session,
        doctor_profile_id: int,
        *,
        only_include_status_ids: Sequence[int] | None = None,
        datetime_range: tuple[datetime, datetime] | None = None,
        order_by_start_datetime_asc: bool | None = None,
    ) -> Sequence[Row[tuple[datetime, datetime, int, str]]]:
        """
        For use by receptionists. Provides importance (urgency) of specialty in the instant.

        :return: (start_datetime, end_datetime, specialty_id, room_name)
        :rtype: Sequence[Row[tuple[datetime, datetime, int, str]]]
        """

        stmt = select(
            Appointment.start_datetime,
            Appointment.end_datetime,
            Appointment.specialty_id,
            Appointment.room_name,
        ).where(Appointment.doctor_profile_id == doctor_profile_id)
        if only_include_status_ids:
            stmt = stmt.where(
                Appointment.appointment_status_id.in_(only_include_status_ids)
            )
        if datetime_range:
            start, end = datetime_range
            stmt = stmt.where(
                Appointment.start_datetime >= start,
                Appointment.end_datetime <= end,
            )
        if order_by_start_datetime_asc is not None:
            stmt = stmt.order_by(
                Appointment.start_datetime.asc()
                if order_by_start_datetime_asc
                else Appointment.start_datetime.desc()
            )
        return session.execute(stmt).all()

    def list_by_created_by_profile_id(
        self,
        session: Session,
        created_by_profile_id: int,
        *,
        only_include_status_ids: Sequence[int] | None = None,
        datetime_range: tuple[datetime, datetime] | None = None,
        order_by_created_datetime_desc: bool | None = None,
        loaders: Sequence[LoaderOption] = (),
    ) -> Sequence[Appointment]:
        stmt = (
            select(Appointment)
            .where(Appointment.created_by_profile_id == created_by_profile_id)
            .options(*loaders)
        )

        if only_include_status_ids:
            stmt = stmt.where(
                Appointment.appointment_status_id.in_(only_include_status_ids)
            )
        if datetime_range:
            start, end = datetime_range
            stmt = stmt.where(
                Appointment.start_datetime >= start,
                Appointment.end_datetime <= end,
            )
        if order_by_created_datetime_desc is not None:
            stmt = stmt.order_by(
                Appointment.created_datetime.desc()
                if order_by_created_datetime_desc
                else Appointment.created_datetime.asc()
            )
        return session.scalars(stmt).all()
