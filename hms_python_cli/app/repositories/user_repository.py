from typing import Sequence

from app.database.models import User
from sqlalchemy import exists, select
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.orm.interfaces import LoaderOption

from .base_repository import BaseRepository


class UserLoad:
    PERSON = joinedload(User.person)


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

    def list_by_person_ids(self, session: Session, person_ids: list[int]) -> list[User]:
        stmt = select(User).where(User.person_id.in_(person_ids))
        return list(session.scalars(stmt))

    def get_by_username(
        self, session: Session, username: str, *, loaders: Sequence[LoaderOption] = ()
    ) -> User | None:
        stmt = select(User).where(User.username == username).options(*loaders)
        return session.scalar(stmt)

    def exists_by_username(self, session: Session, username: str) -> bool:
        stmt = select(exists().where(User.username == username))
        return session.scalar(stmt) or False
