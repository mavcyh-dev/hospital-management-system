from collections.abc import Generator, Callable
from abc import ABC, abstractmethod
from pathlib import Path
from contextlib import contextmanager
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.database.models import Base


class Database(ABC):
    """Abstract database interface - only manages connections"""

    engine: Engine
    session_factory: sessionmaker[Session]

    @abstractmethod
    def _create_engine(self) -> Engine:
        """Create the SQLAlchemy engine (implemented by subclasses)"""
        pass

    def _initialize(self):
        """Initialize engine and session factory"""
        self.engine = self._create_engine()
        self.session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope for a series of operations"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """Close all connections"""
        if self.engine:
            self.engine.dispose()


class MySQLDatabase(Database):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        username: str = "root",
        password: str = "",
        database: str = "myapp",
    ):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self._initialize()

    def _create_engine(self):
        db_url = f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        return create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=5,
            max_overflow=10,
            echo=False,
        )


class SQLiteDatabase(Database):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self._initialize()
        Base.metadata.create_all(bind=self.engine)

    def _create_engine(self):
        db_url = f"sqlite:///{self.db_path}"
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )

        # Enable foreign keys for SQLite
        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine
