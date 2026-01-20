from sqlalchemy.orm import Session
from app.lookups.static_references import (
    PROFILE_TYPES,
    APPOINTMENT_REQUEST_STATUSES,
    APPOINTMENT_STATUSES,
)
from app.lookups.mutable_references import SPECIALTIES


def seed_lookups(session: Session) -> None:
    # Static
    session.add_all(PROFILE_TYPES)
    session.add_all(APPOINTMENT_REQUEST_STATUSES)
    session.add_all(APPOINTMENT_STATUSES)

    # Mutable
    session.add_all(SPECIALTIES)
