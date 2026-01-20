from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, exists
from app.database.models import User
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------
    def get_by_person_id(self, session: Session, person_id: int) -> User | None:
        """Retrieve a user by the related person_id."""
        stmt = select(User).where(User.person_id == person_id)
        return session.scalar(stmt)

    def get_with_person(self, session: Session, user_id: int) -> User | None:
        """Retrieve a user with their related person eagerly loaded."""
        stmt = (
            select(User).options(joinedload(User.person)).where(User.user_id == user_id)
        )
        return session.scalar(stmt)

    def get_by_username(self, session: Session, username: str) -> User | None:
        """Retrieve a user by username."""
        stmt = select(User).where(User.username == username)
        return session.scalar(stmt)

    def get_by_username_with_person(
        self, session: Session, username: str
    ) -> User | None:
        """Retrieve a user by username with person eagerly loaded."""
        stmt = (
            select(User)
            .options(joinedload(User.person))
            .where(User.username == username)
        )
        return session.scalar(stmt)

    def exists_by_username(self, session: Session, username: str) -> bool:
        """Check if a username already exists."""
        stmt = select(exists().where(User.username == username))
        return session.scalar(stmt) or False

    def list_by_person_ids(self, session: Session, person_ids: list[int]) -> list[User]:
        """Retrieve all users associated with given person IDs."""
        stmt = select(User).where(User.person_id.in_(person_ids))
        return list(session.scalars(stmt))
