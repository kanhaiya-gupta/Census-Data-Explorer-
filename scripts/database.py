import os
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy import inspect
import logging
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()
db_conn = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_conn
    db_path = os.getenv("DB_PATH", "data/census.sqlite")
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        raise RuntimeError(f"Database file not found: {db_path}")
    db_conn = DatabaseConnection(db_path)
    logger.info("Database initialized on startup")
    yield
    if db_conn:
        db_conn.close_connection()

app = FastAPI(lifespan=lifespan)

class DatabaseConnection:
    def __init__(self, db_path):
        self.db_path = db_path
        self.engine = None
        self.connection = None
        self.metadata = MetaData()
        self._connect_to_database()

    def _connect_to_database(self):
        try:
            if not os.path.exists(self.db_path):
                logger.error(f"Database file not found: {self.db_path}")
                raise ValueError(f"Database file not found: {self.db_path}")
            self.engine = create_engine(f'sqlite:///{self.db_path}')
            self.connection = self.engine.connect()
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Failed to establish database connection: {e}")
            raise

    def reflect_tables(self):
        try:
            inspector = inspect(self.engine)
            if 'census' not in inspector.get_table_names() or 'state_fact' not in inspector.get_table_names():
                logger.error("Required tables 'census' or 'state_fact' not found")
                raise ValueError("Required tables 'census' or 'state_fact' not found")
            census = Table('census', self.metadata, autoload_with=self.engine)
            state_fact = Table('state_fact', self.metadata, autoload_with=self.engine)
            logger.info("Successfully reflected census and state_fact tables")
            return census, state_fact
        except Exception as e:
            logger.error(f"Error reflecting tables: {e}")
            raise

    def close_connection(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

@app.get("/connect")
async def connect_db():
    try:
        global db_conn
        if not db_conn:
            raise RuntimeError("Database connection not initialized")
        census, state_fact = db_conn.reflect_tables()
        return {"status": "success", "message": "Database connected and tables reflected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)