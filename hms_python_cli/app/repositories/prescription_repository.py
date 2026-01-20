from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, exists
from app.database.models import Prescription
from .base_repository import BaseRepository


class PrescriptionRepository(BaseRepository[Prescription]):
    def __init__(self):
        super().__init__(Prescription)
