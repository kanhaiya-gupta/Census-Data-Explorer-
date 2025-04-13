import os
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy import inspect, insert, update
import matplotlib.pyplot as plt
import logging
import json
from fastapi import FastAPI, HTTPException

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

class DataLoader:
    def __init__(self, connection, engine, results_dir):
        self.engine = engine
        self.connection = connection
        self.metadata = MetaData()
        self.results_dir = results_dir

    def load(self, transformed_data, values_list, census, state_fact):
        logger.info("Starting data loading")
        try:
            if values_list:
                insert_stmt = insert(census)
                result = self.connection.execute(insert_stmt, values_list)
                logger.info(f"Inserted {result.rowcount} records into census table")

            update_stmt = update(state_fact).values(notes='The Wild West') \
                .where(state_fact.c.census_region_name == 'West')
            update_result = self.connection.execute(update_stmt)
            logger.info(f"Updated {update_result.rowcount} records in state_fact table")

            report_content = "# Census Analysis Report\n\n"
            report_content += "## Average Age by Gender\n"
            for sex, avg_age in transformed_data['avg_age']:
                report_content += f"- {sex}: {avg_age:.2f}\n"

            report_content += "\n## Percentage Female by State\n"
            for state, percent in transformed_data['percent_female']:
                report_content += f"- {state}: {percent:.2f}%\n"

            report_content += "\n## Top 10 States by Population Change\n"
            for state, change in transformed_data['pop_change']:
                report_content += f"- {state}: {change:,}\n"

            states = []
            changes = []
            for row in transformed_data['pop_change']:
                try:
                    states.append(str(row[0]))
                    changes.append(int(row[1]))
                except (TypeError, ValueError) as e:
                    logger.warning(f"Invalid pop_change data: {row}, error: {e}")
                    continue
            if not states:
                logger.error("No valid data for plotting")
                raise ValueError("No valid data for plotting")

            plt.figure(figsize=(10, 6))
            plt.bar(states, changes)
            plt.xticks(rotation=45)
            plt.title('Top 10 States by Population Change')
            plt.xlabel('State')
            plt.ylabel('Population Change')
            plt.tight_layout()
            plt.savefig(f'{self.results_dir}/pop_change_plot.png')
            plt.close()

            with open(f'{self.results_dir}/census_report.md', 'w') as f:
                f.write(report_content)

            logger.info("Data loading and report generation completed successfully")
            return report_content
        except Exception as e:
            logger.error(f"Loading failed: {e}")
            raise

@app.post("/load")
async def load_data():
    try:
        db_path = os.getenv("DB_PATH", "data/census.sqlite")
        results_dir = os.getenv("RESULTS_DIR", "results")
        transformed_data_path = os.getenv("TRANSFORMED_DATA_PATH", "data/transformed_data.json")
        
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            raise HTTPException(status_code=500, detail=f"Database file not found: {db_path}")
        if not os.path.exists(transformed_data_path):
            logger.error("Transformed data file not found")
            raise HTTPException(status_code=500, detail="Transformed data file not found")
        if not os.access(results_dir, os.W_OK):
            logger.error(f"No write permission for {results_dir}")
            raise HTTPException(status_code=500, detail=f"No write permission for {results_dir}")
        
        os.makedirs(results_dir, exist_ok=True)
        
        db_conn = DatabaseConnection(db_path)
        census, state_fact = db_conn.reflect_tables()
        
        with open(transformed_data_path, "r") as f:
            data = json.load(f)
            transformed_data = data["transformed_data"]
            values_list = data["values_list"]
        
        loader = DataLoader(db_conn.connection, db_conn.engine, results_dir)
        report_content = loader.load(transformed_data, values_list, census, state_fact)
        
        db_conn.close_connection()
        return {"status": "success", "message": "Data loaded and report generated"}
    except Exception as e:
        logger.error(f"Load endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)