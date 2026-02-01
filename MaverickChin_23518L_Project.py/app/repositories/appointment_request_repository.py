from datetime import datetime
from typing import Sequence

from app.database.models import (
    AppointmentRequest,
    DoctorProfile,
    PatientProfile,
    Profile,
    Specialty,
)
from app.lookups.enums import AppointmentRequestStatusEnum
from sqlalchemy import Row, and_, case, func, select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.interfaces import LoaderOption

from .base_repository import BaseRepository


class AppointmentRequestLoad:
    SPECIALTY = joinedload(AppointmentRequest.specialty)
    PREFERRED_DOCTOR_WITH_PERSON = (
        joinedload(AppointmentRequest.preferred_doctor)
        .joinedload(DoctorProfile.profile)
        .joinedload(Profile.person)
    )
    PATIENT_WITH_PERSON = (
        joinedload(AppointmentRequest.patient)
        .joinedload(PatientProfile.profile)
        .joinedload(Profile.person)
    )
    HANDLED_BY_PROFILE = joinedload(AppointmentRequest.handled_by)


class AppointmentRequestRepository(BaseRepository[AppointmentRequest]):
    def __init__(self):
        super().__init__(AppointmentRequest)

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
    ) -> Sequence[AppointmentRequest]:

        stmt = (
            select(AppointmentRequest)
            .where(AppointmentRequest.patient_profile_id == patient_profile_id)
            .options(*loaders)
        )

        if only_include_status_ids:
            stmt = stmt.where(
                AppointmentRequest.appointment_request_status_id.in_(
                    only_include_status_ids
                )
            )

        if datetime_range:
            start, end = datetime_range
            stmt = stmt.where(
                AppointmentRequest.created_datetime >= start,
                AppointmentRequest.created_datetime <= end,
            )
        if order_by_created_datetime_desc is not None:
            stmt = stmt.order_by(
                AppointmentRequest.created_datetime.desc()
                if order_by_created_datetime_desc
                else AppointmentRequest.created_datetime.asc()
            )
        return session.scalars(stmt).all()

    def list_by_specialty(
        self,
        session: Session,
        specialty_id,
        *,
        only_include_status_ids: Sequence[int] | None = None,
        datetime_range: tuple[datetime, datetime] | None = None,
        order_by_created_datetime_desc: bool | None = None,
        loaders: Sequence[LoaderOption] = (),
    ) -> Sequence[AppointmentRequest]:
        stmt = (
            select(AppointmentRequest)
            .where(AppointmentRequest.specialty_id == specialty_id)
            .options(*loaders)
        )

        if only_include_status_ids:
            stmt = stmt.where(
                AppointmentRequest.appointment_request_status_id.in_(
                    only_include_status_ids
                )
            )
        if datetime_range:
            start, end = datetime_range
            stmt = stmt.where(
                AppointmentRequest.created_datetime >= start,
                AppointmentRequest.created_datetime <= end,
            )
        if order_by_created_datetime_desc is not None:
            stmt = stmt.order_by(
                AppointmentRequest.created_datetime.desc()
                if order_by_created_datetime_desc
                else AppointmentRequest.created_datetime.asc()
            )
        return session.scalars(stmt).all()

    def count_by_specialty(self, session: Session) -> Sequence[Row[tuple[int, int]]]:
        """
        :return: (specialty_id, count)
        :rtype: Sequence[Row[tuple[int, int]]]
        """
        stmt = select(
            AppointmentRequest.specialty_id,
            func.count(AppointmentRequest.appointment_request_id),
        ).group_by(AppointmentRequest.specialty_id)

        results = session.execute(stmt).all()
        return results

    def get_specialty_importance_details(
        self, session: Session
    ) -> Sequence[Row[tuple[int, int, datetime | None, datetime]]]:
        """
        For receptionist use.

        :return: (specialty_id, count, earliest_preferred_datetime, earliest_created_datetime)
        :rtype: Sequence[Row[tuple[int, int, datetime | None, datetime]]]
        """

        earliest_preferred_datetime = func.min(AppointmentRequest.preferred_datetime)
        earliest_created_datetime = func.min(AppointmentRequest.created_datetime)
        appointment_request_count = func.count(
            AppointmentRequest.appointment_request_id
        )

        stmt = (
            select(
                Specialty.specialty_id.label("specialty_id"),
                appointment_request_count,
                earliest_preferred_datetime,
                earliest_created_datetime,
            )
            .outerjoin(
                AppointmentRequest,
                and_(
                    AppointmentRequest.specialty_id == Specialty.specialty_id,
                    AppointmentRequest.appointment_request_status_id
                    == AppointmentRequestStatusEnum.PENDING,
                ),
            )
            .where(Specialty.is_in_service.is_(True))
            .group_by(Specialty.specialty_id)
            .order_by(
                case((earliest_preferred_datetime == None, 1), else_=0),
                earliest_preferred_datetime,
                case((earliest_created_datetime == None, 1), else_=0),
                earliest_created_datetime,
                appointment_request_count.desc(),
            )
        )
        results = session.execute(stmt).all()
        return results
