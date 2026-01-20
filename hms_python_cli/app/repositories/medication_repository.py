from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, exists
from app.database.models import Medication
from .base_repository import BaseRepository


class MedicationRepository(BaseRepository[Medication]):
    def __init__(self):
        super().__init__(Medication)
