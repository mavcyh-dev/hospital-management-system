from typing import TYPE_CHECKING, Optional, List
from datetime import datetime, date
from sqlalchemy import (
    String,
    Integer,
    SmallInteger,
    DateTime,
    Date,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .profiles import Profile


class User(Base):
    """User entity - authentication and authorization"""

    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("person.person_id"), unique=True
    )
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_datetime: Mapped[datetime] = mapped_column(DateTime)
    is_in_service: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    person: Mapped["Person"] = relationship("Person", back_populates="user")


class Person(Base):
    """Person entity - stores demographic information

    ISO/IEC 5218 sex codes: 0=Unknown, 1=Male, 2=Female, 9=Not applicable
    """

    __tablename__ = "person"

    person_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    sex: Mapped[int] = mapped_column(SmallInteger, default=0)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    date_of_birth: Mapped[date] = mapped_column(Date)
    primary_email: Mapped[str] = mapped_column(String(254))
    primary_phone_number: Mapped[str] = mapped_column(String(32))
    primary_home_address: Mapped[str] = mapped_column(String(255))
    is_in_service: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="person", uselist=False
    )
    profiles: Mapped[List["Profile"]] = relationship("Profile", back_populates="person")
