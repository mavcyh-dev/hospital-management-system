from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, exists
from app.database.models import Appointment
from .base_repository import BaseRepository


class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self):
        super().__init__(Appointment)
