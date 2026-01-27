from datetime import date

from app.database.models import Person
from app.repositories.person_repository import PersonRepository
from app.repositories.user_repository import UserRepository
from app.services.base_service import BaseService
from sqlalchemy.orm import Session


class PersonService(BaseService[Person]):
    def __init__(
        self,
        person_repo: PersonRepository,
        user_repo: UserRepository,
    ):
        super().__init__(person_repo)
        self.person_repo = person_repo
        self.user_repo = user_repo

    # -------------------------------------------------------------------------
    # CREATE to be handled by UserService
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # READ
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------------------

    def update_person_info(
        self,
        session: Session,
        person_id: int,
        sex: int | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        date_of_birth: date | None = None,
        primary_email: str | None = None,
        primary_phone_number: str | None = None,
        primary_home_address: str | None = None,
    ) -> Person:
        """Update person's editable information."""
        person = self.person_repo.get(session, person_id)
        if not person:
            raise ValueError(f"Person with id {person_id} not found")
        if sex is not None:
            person.sex = sex
        if first_name is not None:
            person.first_name = first_name
        if last_name is not None:
            person.last_name = last_name
        if date_of_birth is not None:
            person.date_of_birth = date_of_birth
        if primary_email is not None:
            person.primary_email = primary_email
        if primary_phone_number is not None:
            person.primary_phone_number = primary_phone_number
        if primary_home_address is not None:
            person.primary_home_address = primary_home_address

        return self.person_repo.update(session, person)

    # -------------------------------------------------------------------------
    # DELETE
    # -------------------------------------------------------------------------
