from sqlalchemy.orm import declarative_base,sessionmaker
from sqlalchemy import create_engine


DATABASE_URL = ""

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base  = declarative_base()


async def get_db():
    try:
        db = SessionLocal()
        yield db

    finally:
        db.close()