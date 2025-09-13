from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.core.config import DATABASE_URL_LOCAL

engine = create_async_engine(DATABASE_URL_LOCAL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    