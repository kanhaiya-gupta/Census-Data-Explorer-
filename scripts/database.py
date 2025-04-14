import os
from sqlalchemy import create_engine, MetaData, Table, select, func
from sqlalchemy import inspect
import logging
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global database connection variable
db_conn = None

# Database connection class
class DatabaseConnection:
    def __init__(self, db_path):
        self.db_path = db_path
        self.engine = None
        self.connection = None
        self.metadata = MetaData()
        self._connect_to_database()

    def _connect_to_database(self):
        try:
            logger.info(f"Attempting to connect to {self.db_path}")
            if not os.path.exists(self.db_path):
                logger.error(f"Database file not found: {self.db_path}")
                raise ValueError(f"Database file not found: {self.db_path}")
                
            # Create SQLite URL with proper path
            sqlite_url = f'sqlite:///{self.db_path}'
            logger.info(f"Using SQLite URL: {sqlite_url}")
            
            # Create engine with echo=True for debugging
            self.engine = create_engine(sqlite_url, echo=True)
            self.connection = self.engine.connect()
            logger.info("Database connection established successfully")
            
            # Check tables
            inspector = inspect(self.engine)
            table_names = inspector.get_table_names()
            logger.info(f"Tables found: {table_names}")
            
        except Exception as e:
            logger.error(f"Failed to establish database connection: {str(e)}", exc_info=True)
            raise

    def reflect_tables(self):
        try:
            inspector = inspect(self.engine)
            table_names = inspector.get_table_names()
            logger.info(f"Found tables: {table_names}")
            
            if not table_names:
                logger.error("No tables found in the database")
                raise ValueError("No tables found in the database")
                
            if 'census' not in table_names or 'state_fact' not in table_names:
                logger.error("Required tables 'census' or 'state_fact' not found")
                raise ValueError("Required tables 'census' or 'state_fact' not found")
                
            census = Table('census', self.metadata, autoload_with=self.engine)
            state_fact = Table('state_fact', self.metadata, autoload_with=self.engine)
            logger.info("Successfully reflected census and state_fact tables")
            return census, state_fact
        except Exception as e:
            logger.error(f"Error reflecting tables: {str(e)}", exc_info=True)
            raise

    def close_connection(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

# Initialize database connection
def init_db():
    global db_conn
    db_path = os.getenv("DB_PATH", "/data/census.sqlite")
    logger.info(f"Initializing database connection to {db_path}")
    try:
        # Check if directory exists
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            logger.error(f"Database directory not found: {db_dir}")
            raise RuntimeError(f"Database directory not found: {db_dir}")
            
        # Check if file exists
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            raise RuntimeError(f"Database file not found: {db_path}")
            
        # Check file permissions
        file_stat = os.stat(db_path)
        logger.info(f"File permissions: {file_stat.st_mode:o}")
        logger.info(f"File owner: {file_stat.st_uid}")
        logger.info(f"File group: {file_stat.st_gid}")
        
        # Initialize database connection
        db_conn = DatabaseConnection(db_path)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise

# Lifespan function to manage startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    if db_conn:
        db_conn.close_connection()
        logger.info("Database connection closed on shutdown")

# Create the FastAPI app using the lifespan function
app = FastAPI(lifespan=lifespan)

# API endpoint to connect to the DB and reflect tables
@app.get("/connect")
async def connect_db():
    try:
        global db_conn
        if not db_conn:
            logger.error("Database connection not initialized")
            raise RuntimeError("Database connection not initialized")
        census, state_fact = db_conn.reflect_tables()
        return {"status": "success", "message": "Database connected and tables reflected"}
    except Exception as e:
        logger.error(f"Connect endpoint failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        db_path = os.getenv("DB_PATH", "/data/census.sqlite")
        if not os.path.exists(db_path):
            raise HTTPException(status_code=503, detail="Database file not found")
        
        db_conn = DatabaseConnection(db_path)
        census, state_fact = db_conn.reflect_tables()
        db_conn.close_connection()
        
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))

# Run with uvicorn when executed directly
if __name__ == "__main__":
    import uvicorn
    init_db()  # Initialize database before starting the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
