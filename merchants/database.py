from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from merchants.config import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    pool_recycle=1800,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
DatabaseModel = declarative_base()
