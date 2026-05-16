from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from ..config import DATABASE_URL

#SQLAlchemy Engine:
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # DB session factory

Base = declarative_base()  # Base for models to inherit from

#Dependency function to get DB session
def get_db():
    """
    Yields a db session and closes it as soon as the request is finished.
    Used for the FastAPI Depends() injection.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Initialization function to create tables
def init_db():
    """
    Creates tables in DB if it doesn't exits.
    Once called when the FastAPI application starts.
    """
    Base.metadata.create_all(bind = engine) #Call it after the models are imported in the main app file 