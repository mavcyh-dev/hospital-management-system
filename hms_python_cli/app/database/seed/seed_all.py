"""Database seeding utilities"""

from app.database.engine import Database
from app.core.app import Services

from app.database.seed.seed_lookups import seed_lookups
from app.database.seed.seed_tables import seed_tables


def seed_all(db: Database, services: Services):
    with db.session_scope() as session:
        seed_lookups(session)
        seed_tables(session, services)
        session.commit()
