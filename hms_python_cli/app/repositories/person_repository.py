from app.database.models import Person, Profile, User
from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from .base_repository import BaseRepository


class PersonRepository(BaseRepository[Person]):
    def __init__(self):
        super().__init__(Person)

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------
    def get_by_user_id(self, session: Session, user_id: int) -> Person | None:
        """Retrieve a person by the related user_id."""
        stmt = select(Person).join(User).where(User.user_id == user_id)
        return session.scalar(stmt)

    def get_by_email(self, session: Session, email: str) -> Person | None:
        """Get person by email"""
        stmt = select(Person).where(Person.primary_email == email)
        return session.scalar(stmt)

    def search_by_name(
        self, session: Session, search_term: str, skip: int = 0, limit: int = 100
    ) -> list[Person]:
        """Search persons by first or last name"""
        search_pattern = f"%{search_term}%"
        stmt = (
            select(Person)
            .where(
                or_(
                    Person.first_name.ilike(search_pattern),
                    Person.last_name.ilike(search_pattern),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return list(session.scalars(stmt).all())

    def exists_by_profile_type(
        self, session: Session, person_id: int, profile_type_id: int
    ) -> bool:
        """Check if a profile type exists for given person_id."""
        stmt = select(
            exists().where(
                Profile.person_id == person_id,
                Profile.profile_type_id == profile_type_id,
            )
        )
        return bool(session.scalar(stmt))
