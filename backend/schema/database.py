from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base

USER = "postgres"
PASSWORD = "postgres"
ADDRESS = "localhost"
PORT = 5432
DB = "furalert"

DATABASE_URL= f"postgresql://{USER}:{PASSWORD}@{ADDRESS}:{PORT}/{DB}"

# set echo=True to see what SQL commands were done
engine = create_engine(DATABASE_URL, echo=True)

Base = declarative_base() # inherit from this class to create ORM models

def get_db_session():
    try:
        dbsessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db_session = dbsessionmaker()
        return db_session
    except:
        db_session.rollback()
        raise
    finally:
        db_session.close()