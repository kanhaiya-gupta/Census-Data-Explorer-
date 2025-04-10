from sqlalchemy import create_engine
from src.config import DATABASE_URL

def connect_to_db():
    engine = create_engine(DATABASE_URL)
    return engine
