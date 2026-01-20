from datetime import datetime, date
from sqlalchemy.orm import Session

from app.database.models import User, Person
from app.repositories.user_repository import UserRepository
from app.repositories.person_repository import PersonRepository
from app.services.base_service import BaseService
from app.services.security_service import SecurityService
from app.lookups.enums import ProfileTypeEnum, SexEnum


class UserService(BaseService[User]):
    """Handles business logic related to users."""

    def __init__(
        self,
        user_repo: UserRepository,
        person_repo: PersonRepository,
        security_service: SecurityService,
    ):
        super().__init__(user_repo)
        self.user_repo = user_repo
        self.person_repo = person_repo
        self.security_service = security_service

    # -------------------------------------------------------------------------
    # CREATE
    # -------------------------------------------------------------------------
    def create_user(
        self,
        session: Session,
        username: str,
        plain_password: str,
        first_name: str,
        last_name: str,
        date_of_birth: date,
        primary_email: str,
        primary_phone_number: str,
        primary_home_address: str,
        sex: int | None = SexEnum.UNKNOWN.value,
    ) -> User:
        """Create a new user with associated person record."""
        if self.user_repo.exists_by_username(session, username):
            raise ValueError(f"Username '{username}' already exists")

        # Create person first
        person = Person(
            sex=sex,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            primary_email=primary_email,
            primary_phone_number=primary_phone_number,
            primary_home_address=primary_home_address,
        )
        person = self.person_repo.add(session, person)

        # Create user with hashed password
        user = User(
            person_id=person.person_id,
            username=username,
            password_hash=self.security_service.hash_password(plain_password),
            created_datetime=datetime.now(),
        )

        return self.user_repo.add(session, user)

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------
    def exists_by_username(self, session: Session, username: str) -> bool:
        """Check if a username already exists."""
        return self.user_repo.exists_by_username(session, username)

    def has_profile_type(
        self,
        session: Session,
        user_id: int,
        profile_type: ProfileTypeEnum,
    ) -> bool:
        """Check if user has a specific profile type."""
        user = self.user_repo.get_with_person(session, user_id)
        if not user:
            raise ValueError(f"User '{user_id}' does not exist")

        return self.person_repo.exists_by_profile_type(
            session, user.person_id, profile_type
        )

    def get_with_person(
        self,
        session: Session,
        user_id: int,
    ) -> User | None:
        """Retrieve user with person details eagerly loaded."""
        return self.user_repo.get_with_person(session, user_id)

    def get_by_username(
        self,
        session: Session,
        username: str,
    ) -> User | None:
        """Retrieve user by username."""
        return self.user_repo.get_by_username(session, username)

    def get_by_username_with_person(
        self,
        session: Session,
        username: str,
    ) -> User | None:
        """Retrieve user by username with person details eagerly loaded."""
        return self.user_repo.get_by_username_with_person(session, username)

    def validate_password(
        self,
        session: Session,
        user_id: int,
        plain_password: str,
    ) -> bool:
        """Check if the password matches that of the user."""
        user = self.user_repo.get(session, user_id)
        if user is None:
            return False
        return self.security_service.verify_password(plain_password, user.password_hash)

    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------
    def change_password(
        self,
        session: Session,
        user_id: int,
        new_plain_password: str,
    ) -> User:
        """Change a user's password."""
        user = self.user_repo.get(session, user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        user.password_hash = self.security_service.hash_password(new_plain_password)
        return self.user_repo.update(session, user)

    # -------------------------------------------------------------------------
    # DELETE
    # -------------------------------------------------------------------------
    def delete_user(self, session: Session, user_id: int) -> None:
        """Delete user and associated person record."""
        user = self.user_repo.get(session, user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        person_id = user.person_id

        # Delete user first (respects FK constraints)
        self.user_repo.delete(session, user)

        # Delete orphaned person record
        person = self.person_repo.get(session, person_id)
        if person:
            self.person_repo.delete(session, person)
