from typing import TypeVar, Generic, Sequence
from sqlalchemy.orm import Session
from sqlalchemy.orm.interfaces import LoaderOption
from sqlalchemy import select, inspect

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with session-per-operation pattern.

    Naming conventions:
    - add() - creates a new entity
    - get() - retrieves by primary key
    - get_by_X() - retrieves by specific field
    - get_all() - retrieves all entities
    - exists() / exists_by_X() - checks existence
    - update() - updates existing entity
    - delete() - removes entity
    - list() / list_by_X() - returns multiple entities with optional filtering
    """

    def __init__(self, model: type[T]):
        self.model = model

    def _get_pk_column(self, session: Session):
        mapper = inspect(self.model)
        if mapper is None:
            raise RuntimeError("Could not inspect model.")
        pk_cols = mapper.primary_key
        if len(pk_cols) != 1:
            raise ValueError("Composite primary keys not supported.")
        else:
            return pk_cols[0]

    # -------------------------------------------------------------------------
    # CREATE
    # -------------------------------------------------------------------------
    def add(self, session: Session, entity: T) -> T:
        """Add a new entity to the session and flush to get ID."""
        session.add(entity)
        session.flush()
        session.refresh(entity)
        return entity

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------

    def get(
        self, session: Session, id: int, *, loaders: Sequence[LoaderOption] = ()
    ) -> T | None:
        """Retrieve an entity by primary key with optional eager loading."""
        stmt = (
            select(self.model)
            .where(self._get_pk_column(session) == id)
            .options(*loaders)
        )
        return session.scalar(stmt)

    def get_all(self, session: Session) -> list[T]:
        """Retrieve all entities of this model."""
        stmt = select(self.model)
        return list(session.scalars(stmt))

    def get_first_by(self, session: Session, **filters) -> T | None:
        """Get the first entity matching filters."""
        stmt = select(self.model).filter_by(**filters)
        return session.scalars(stmt).first()

    def list_by(self, session: Session, **filters) -> list[T]:
        """Get all entities matching filters."""
        stmt = select(self.model).filter_by(**filters)
        return list(session.scalars(stmt))

    def exists(self, session: Session, id: int) -> bool:
        """Check if an entity exists by primary key."""
        return session.get(self.model, id) is not None

    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------
    def update(self, session: Session, entity: T) -> T:
        """Merge changes of a detached entity into the session."""
        updated_entity = session.merge(entity)
        session.flush()
        session.refresh(updated_entity)
        return updated_entity

    # -------------------------------------------------------------------------
    # DELETE
    # -------------------------------------------------------------------------
    def delete(self, session: Session, entity: T) -> None:
        """Delete an entity from the session."""
        session.delete(entity)
        session.flush()

    def delete_by_id(self, session: Session, id: int) -> None:
        """Deletes an entity from the session by primary key."""
        entity = self.get(session, id)
        if entity is None:
            raise ValueError(f"Entity id {id} does not exist")
        self.delete(session, entity)
