from typing import Sequence

from app.database.models import Person, User
from sqlalchemy import exists, select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.interfaces import LoaderOption

from .base_repository import BaseRepository


class UserLoad:
    PERSON = joinedload(User.person)
    PERSON_WITH_PROFILES = joinedload(User.person).joinedload(Person.profiles)


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------
    def get_by_person_id(
        self, session: Session, person_id: int, *, loaders: Sequence[LoaderOption] = ()
    ) -> User | None:
        stmt = select(User).where(User.person_id == person_id).options(*loaders)
        return session.scalar(stmt)

    def get_by_username(
        self, session: Session, username: str, *, loaders: Sequence[LoaderOption] = ()
    ) -> User | None:
        stmt = select(User).where(User.username == username).options(*loaders)
        return session.scalar(stmt)

    def exists_by_username(
        self, session: Session, username: str, is_in_service: bool = False
    ) -> bool:
        conditions = [User.username == username]

        if is_in_service:
            conditions.append(User.is_in_service.is_(True))

        stmt = select(exists().where(*conditions))
        return bool(session.scalar(stmt))
