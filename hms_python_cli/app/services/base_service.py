from typing import TypeVar, Generic
from sqlalchemy.orm import Session

from app.repositories.base_repository import BaseRepository

T = TypeVar("T")


class BaseService(Generic[T]):
    """Base service for common CRUD operations.

    Services orchestrate business logic and coordinate between repositories.
    For simple entities, this can wrap repository calls. For complex operations,
    override or add methods with business logic.

    Naming conventions:
    - create_X() - creates new entity/entities (applies validation/business rules)
    - get_by_id() / get_by_X() - retrieves entity (wraps repository, may add logic)
    - get_X_with_Y() - retrieves with eager-loaded relationships
    - list_X() / list_by_X() - retrieves multiple entities (may apply filtering/sorting)
    - exists() / exists_by_X() - checks existence (wraps repository)
    - update_X() - updates entity (applies validation/business rules)
    - change_X() - specialized update for specific field (e.g., change_password)
    - delete_X() - removes entity (may handle cascades/cleanup)
    - has_X() - checks boolean state (e.g., has_profile, has_permission)
    - can_X() - checks authorization/ability (e.g., can_book_appointment)
    - validate_X() - validation without mutation (e.g., validate_availability)
    """

    def __init__(self, repo: BaseRepository[T]):
        self.repo = repo

    # -------------------------------------------------------------------------
    # CREATE
    # -------------------------------------------------------------------------
    def create(self, session: Session, entity: T) -> T:
        """Create a new entity with any business logic validation."""
        # Override this method to add validation, business rules, etc.
        return self.repo.add(session, entity)

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------
    def get_by_id(self, session: Session, id: int) -> T | None:
        """Retrieve entity by ID."""
        return self.repo.get(session, id)

    def get_all(self, session: Session) -> list[T]:
        """Retrieve all entities."""
        return self.repo.get_all(session)

    def exists(self, session: Session, id: int) -> bool:
        """Check if entity exists."""
        return self.repo.exists(session, id)

    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------
    def update(self, session: Session, entity: T) -> T:
        """Update an entity with business logic validation."""
        # Override to add validation, authorization checks, etc.
        return self.repo.update(session, entity)

    # -------------------------------------------------------------------------
    # DELETE
    # -------------------------------------------------------------------------
    def delete(self, session: Session, entity: T) -> None:
        """Delete an entity with business logic checks."""
        # Override to add cascade logic, authorization, etc.
        self.repo.delete(session, entity)

    def delete_by_id(self, session: Session, id: int) -> None:
        """Delete an entity by ID."""
        entity = self.get_by_id(session, id)
        if not entity:
            raise ValueError(f"Entity with id {id} not found")
        self.delete(session, entity)
