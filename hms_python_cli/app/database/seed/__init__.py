from app.database.seed.manual import seed_manual
from app.database.seed.random import seed_random
from app.database.seed.lookups import seed_lookups
from app.database.engine import Database
from app.core.app import Repos, Services


def seed_all(db: Database, repos: Repos, services: Services) -> None:

    with db.session_scope() as session:
        seed_lookups(session)
        seed_manual(session, repos, services)
        seed_random(session)
