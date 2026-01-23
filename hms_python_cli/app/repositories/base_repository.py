from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import and_, exists, func, inspect, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.interfaces import LoaderOption

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with condition-based querying only."""

    def __init__(self, model: type[T]):
        self.model = model

    # -------------------------------------------------------------------------
    # INTERNAL
    # -------------------------------------------------------------------------
    def _get_pk_column(self, session: Session):
        mapper = inspect(self.model)
        if mapper is None:
            raise RuntimeError("Could not inspect model.")
        pk_cols = mapper.primary_key
        if len(pk_cols) != 1:
            raise ValueError("Composite primary keys not supported.")
        return pk_cols[0]

    # -------------------------------------------------------------------------
    # CREATE
    # -------------------------------------------------------------------------
    def add(self, session: Session, entity: T) -> T:
        """Add a new entity; flush to get DB-generated fields (e.g. ID)."""
        session.add(entity)
        session.flush()
        session.refresh(entity)
        return entity

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------

    def get(
        self,
        session: Session,
        id: int,
        *,
        conditions: Sequence[Any] = (),
        loaders: Sequence[LoaderOption] = (),
    ) -> T | None:
        pk = self._get_pk_column(session)
        stmt = select(self.model).where(and_(pk == id, *conditions)).options(*loaders)
        return session.scalar(stmt)

    def get_all(
        self,
        session: Session,
        *,
        conditions: Sequence[Any] = (),
        limit: int | None = 100,
        loaders: Sequence[LoaderOption] = (),
        order_by: Sequence[Any] = (),
        offset: int | None = None,
    ) -> Sequence[T]:
        stmt = select(self.model).options(*loaders)

        if conditions:
            stmt = stmt.where(*conditions)

        if order_by:
            stmt = stmt.order_by(*order_by)

        if offset:
            stmt = stmt.offset(offset)

        if limit is not None:
            stmt = stmt.limit(limit)

        return session.scalars(stmt).all()

    def get_first(
        self,
        session: Session,
        *,
        conditions: Sequence[Any] = (),
        loaders: Sequence[LoaderOption] = (),
        order_by: Sequence[Any] = (),
    ) -> T | None:
        stmt = select(self.model).options(*loaders)

        if conditions:
            stmt = stmt.where(*conditions)

        if order_by:
            stmt = stmt.order_by(*order_by)

        return session.scalars(stmt).first()

    def list(
        self,
        session: Session,
        *,
        conditions: Sequence[Any] = (),
        loaders: Sequence[LoaderOption] = (),
        order_by: Sequence[Any] = (),
    ) -> list[T]:
        stmt = select(self.model).options(*loaders)

        if conditions:
            stmt = stmt.where(*conditions)

        if order_by:
            stmt = stmt.order_by(*order_by)

        return list(session.scalars(stmt))

    def exists(
        self, session: Session, id: int, *, conditions: Sequence[Any] = ()
    ) -> bool:
        """Check existence via GET."""
        return self.get(session, id) is not None

    def exists_with_conditions(
        self, session: Session, conditions: Sequence[Any] = ()
    ) -> bool:
        """Check existence of object with conditions."""
        stmt = select(exists().where(*conditions))
        return session.scalar(stmt) or False

    def count(
        self,
        session: Session,
        *,
        conditions: Sequence[Any] = (),
    ) -> int:
        """
        Count rows of this model with optional conditions.
        """
        stmt = select(func.count()).select_from(self.model)
        if conditions:
            stmt = stmt.where(*conditions)

        return session.scalar(stmt) or 0

    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------
    def update(self, session: Session, entity: T) -> T:
        """Merge changes of a detached entity."""
        merged = session.merge(entity)
        session.flush()
        session.refresh(merged)
        return merged

    # -------------------------------------------------------------------------
    # DELETE
    # -------------------------------------------------------------------------
    def delete(self, session: Session, entity: T) -> None:
        session.delete(entity)
        session.flush()

    def delete_by_id(self, session: Session, id: int) -> None:
        entity = self.get(session, id)
        if not entity:
            raise ValueError(f"Entity id {id} does not exist")
        self.delete(session, entity)
