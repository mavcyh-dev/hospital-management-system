from app.core.app import Repos, Services
from app.database.engine import Database
from app.database.seed.lookups import seed_lookups
from app.database.seed.medications import seed_medications
from app.database.seed.default_users import seed_default_users
from app.database.seed.random_users import seed_users_random


def seed_development(db: Database, repos: Repos, services: Services, seed: int) -> None:

    with db.session_scope() as session:
        print(f"[DEV seed] Starting seed. Seed value: {seed}")
        seed_lookups(session)
        seed_medications(session)
        seed_users_random(
            session,
            seed,
            patients_count=1000,
            doctors_count=300,
            receptionists_count=20,
            admins_count=0,
        )
        seed_default_users(session, seed, repos, services)


def seed_production(db: Database, repos: Repos, services: Services, seed: int) -> None:
    with db.session_scope() as session:
        print("[PROD seed] Starting seed.")
        seed_lookups(session)
        seed_medications(session)
        seed_default_users(session, seed, repos, services)
