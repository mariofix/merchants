from sqlmodel import Session, create_engine, select
from merchants.config import settings


engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_recycle=1800,
    pool_pre_ping=True,
)
