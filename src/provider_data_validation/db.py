from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.types import JSON as JSONType
from .config import settings


# Minimal SQLAlchemy setup. Call `init_db()` during deploy/migrations.
DATABASE_URL = settings.database_url
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class VerificationSessionDB(Base):
    __tablename__ = "verification_sessions"
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(String(128), index=True)
    session_key = Column(String(256), index=True, unique=True)
    data = Column(JSONType)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
