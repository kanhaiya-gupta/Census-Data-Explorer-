import pandas as pd
import logging
from sqlalchemy import create_engine, MetaData, Table, select, func, case, cast, Float, desc
from sqlalchemy import inspect
from fastapi import FastAPI, HTTPException
import json
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()

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

class DataTransformer:
    def __init__(self, connection, census, state_fact):
        self.connection = connection
        self.census = census
        self.state_fact = state_fact

    def transform(self, census_df):
        logger.info("Starting data transformation")
        transformed_data = {}
        try:
            avg_age_stmt = select(
                self.census.c.sex,
                (func.sum(self.census.c.pop2000 * self.census.c.age) /
                 func.sum(self.census.c.pop2000)).label('average_age')
            ).group_by(self.census.c.sex)
            avg_age_results = self.connection.execute(avg_age_stmt).fetchall()

            percent_female_stmt = select(
                self.census.c.state,
                (func.sum(case(
                    (self.census.c.sex == 'F', self.census.c.pop2000),
                    else_=0)) /
                 cast(func.sum(self.census.c.pop2000), Float) * 100).label('percent_female')
            ).group_by(self.census.c.state)
            percent_female_results = self.connection.execute(percent_female_stmt).fetchall()

            pop_change_stmt = select(
                self.census.c.state,
                (func.sum(self.census.c.pop2008) - func.sum(self.census.c.pop2000)).label('pop_change')
            ).group_by(self.census.c.state).order_by(desc('pop_change')).limit(10)
            pop_change_results = self.connection.execute(pop_change_stmt).fetchall()

            transformed_data['avg_age'] = [(row[0], float(row[1])) for row in avg_age_results]
            transformed_data['percent_female'] = [(row[0], float(row[1])) for row in percent_female_results]
            transformed_data['pop_change'] = [(row[0], int(row[1])) for row in pop_change_results]

            values_list = []
            for row in census_df.to_dict('records'):
                try:
                    values_list.append({
                        'state': str(row['state']),
                        'sex': str(row['sex']),
                        'age': int(row['age']),
                        'pop2000': int(row['pop2000']),
                        'pop2008': int(row['pop2008'])
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid data in row: {row}, error: {e}")
                    continue

            logger.info("Data transformation completed successfully")
            return transformed_data, values_list
        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            raise

@app.post("/transform")
async def transform_data():
    try:
        db_path = os.getenv("DB_PATH", "data/census.sqlite")
        csv_path = os.getenv("CSV_PATH", "data/census.csv")
        output_file = os.getenv("TRANSFORMED_DATA_PATH", "data/transformed_data.json")
        
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            raise HTTPException(status_code=500, detail=f"CSV file not found: {csv_path}")
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            raise HTTPException(status_code=500, detail=f"Database file not found: {db_path}")

        output_dir = os.path.dirname(output_file)
        os.makedirs(output_dir, exist_ok=True)
        if not os.access(output_dir, os.W_OK):
            logger.error(f"No write permission for {output_dir}")
            raise HTTPException(status_code=500, detail=f"No write permission for {output_dir}")

        db_conn = DatabaseConnection(db_path)
        census, state_fact = db_conn.reflect_tables()
        
        census_df = pd.read_csv(csv_path, header=None)
        census_df.columns = ['state', 'sex', 'age', 'pop2000', 'pop2008']
        
        transformer = DataTransformer(db_conn.connection, census, state_fact)
        transformed_data, values_list = transformer.transform(census_df)
        
        with open(output_file, "w") as f:
            json.dump({
                "transformed_data": transformed_data,
                "values_list": values_list
            }, f)
        
        db_conn.close_connection()
        return {"status": "success", "message": "Data transformed and saved"}
    except Exception as e:
        logger.error(f"Transform endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)