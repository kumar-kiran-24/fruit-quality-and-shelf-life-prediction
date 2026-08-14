import os
from pathlib import Path

from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker




PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

ENV_FILE = (
    PROJECT_ROOT /
    ".env"
)

load_dotenv(
    ENV_FILE
)




DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not DATABASE_URL:

    raise RuntimeError(
        "DATABASE_URL is not configured "
        "in the .env file."
    )




engine = create_engine(

    DATABASE_URL,

    pool_pre_ping=True,

    echo=False
)



SessionLocal = sessionmaker(

    bind=engine,

    autocommit=False,

    autoflush=False
)




Base = declarative_base()




def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()