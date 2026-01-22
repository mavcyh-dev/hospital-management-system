import re
from datetime import datetime, date, time
from sqlalchemy.orm import Session
from typing import Callable, ContextManager
import operator

from app.ui.input_result import InputResult
from app.services.user_service import UserService

from app.lookups.enums import ProfileTypeEnum

OP_DISPLAY = {
    operator.gt: ">",
    operator.ge: "≥",
    operator.lt: "<",
    operator.le: "≤",
    operator.eq: "=",
    operator.ne: "≠",
}


def validate_password(raw: str) -> InputResult:
    if len(raw) < 6:
        return InputResult(value=raw, error="Must be > 6 characters long")
    return InputResult(value=raw)


def validate_email(raw: str) -> InputResult:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if re.match(pattern, raw):
        return InputResult(value=raw)
    return InputResult(value=raw, error="Invalid email format")


def validate_phone_number(raw: str) -> InputResult:
    pattern = r"^\+?\d[\d\s-]{6,14}\d$"
    if re.match(pattern, raw):
        return InputResult(value=raw)
    return InputResult(value=raw, error="Invalid phone number")


def validate_date(raw: str) -> InputResult:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            dt = datetime.strptime(raw, fmt).date()
            return InputResult(value=dt, display_value=dt.isoformat())
        except ValueError:
            continue
    return InputResult(value=raw, error="Invalid date format (expected YYYY-MM-DD)")


def validate_date_relation(
    value: date,
    other: date,
    op: Callable[[date, date], bool],
) -> InputResult:
    ok = op(value, other)

    return InputResult(
        value=value,
        display_value=value.isoformat(),
        error=None if ok else f"Date must be {OP_DISPLAY[op]} {other}",
    )


def validate_date_in_range(
    value: date,
    start: date,
    end: date,
    inclusive: bool,
) -> InputResult:

    if inclusive:
        ok = start <= value <= end
        display = f">= {start} and <= {end}"
    else:
        ok = start < value < end
        display = f"> {start} and < {end}"

    return InputResult(
        value=value,
        display_value=value.isoformat(),
        error=None if ok else f"Date must be {display}",
    )


def validate_time(raw: str) -> InputResult:
    for fmt in ("%H:%M", "%H%M", "%H.%M"):
        try:
            t = datetime.strptime(raw, fmt).time()
            return InputResult(value=t, display_value=t.strftime("%H:%M"))
        except ValueError:
            continue
    return InputResult(value=raw, error="Invalid time format (expected HH:MM)")


def validate_user_exists_for_username(
    raw: str,
    session_scope: Callable[[], ContextManager[Session]],
    user_service: UserService,
    inverse: bool | None = None,
) -> InputResult:
    with session_scope() as session:
        exists = user_service.user_repo.exists_by_username(session, raw)

    if inverse:
        return InputResult(
            value=raw, error="Username already exists" if exists else None
        )
    else:
        return InputResult(
            value=raw, error=None if exists else "Username does not exist"
        )


def validate_profile_exists_for_username(
    raw: str,
    session_scope: Callable[[], ContextManager[Session]],
    user_service: UserService,
    profile_type: ProfileTypeEnum,
) -> InputResult:
    with session_scope() as session:
        user = user_service.user_repo.get_by_username(session, username=raw)
        if not user:
            return InputResult(value=raw, error="Username does not exist")
        elif user_service.person_repo.exists_by_profile_type(
            session, user.person_id, profile_type
        ):
            return InputResult(value=raw)
        else:
            return InputResult(value=raw, error="Profile type not found for user")
