import pandas as pd
import logging
from sqlalchemy import create_engine, MetaData, Table, select, func, case, cast, Float, desc, insert, update
from sqlalchemy import inspect
from fastapi import FastAPI, HTTPException
import json
import os
import matplotlib.pyplot as plt

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
    def __init__(self, connection, census, state_fact, results_dir):
        self.connection = connection
        self.census = census
        self.state_fact = state_fact
        self.results_dir = results_dir

    def load_data(self, values_list, transformed_data):
        logger.info("Starting data loading")
        try:
            if values_list:
                insert_stmt = insert(self.census)
                result = self.connection.execute(insert_stmt, values_list)
                logger.info(f"Inserted {result.rowcount} records into census table")

            update_stmt = update(self.state_fact).values(notes='The Wild West') \
                .where(self.state_fact.c.census_region_name == 'West')
            update_result = self.connection.execute(update_stmt)
            logger.info(f"Updated {update_result.rowcount} records in state_fact table")

            # Generate JSON report
            report = {}
            
            # Total population by state
            pop_by_state = select(
                self.census.c.state,
                func.sum(self.census.c.pop2008).label('total_population')
            ).group_by(self.census.c.state)
            report['population_by_state'] = [
                (row[0], int(row[1])) for row in self.connection.execute(pop_by_state).fetchall()
            ]
            
            # Age distribution
            age_dist = select(
                self.census.c.age,
                func.sum(self.census.c.pop2008).label('population')
            ).group_by(self.census.c.age)
            report['age_distribution'] = [
                (int(row[0]), int(row[1])) for row in self.connection.execute(age_dist).fetchall()
            ]
            
            # Gender ratio by state
            gender_ratio = select(
                self.census.c.state,
                (func.sum(case((self.census.c.sex == 'F', self.census.c.pop2008), else_=0)) /
                 func.sum(case((self.census.c.sex == 'M', self.census.c.pop2008), else_=0))).label('gender_ratio')
            ).group_by(self.census.c.state)
            report['gender_ratio'] = [
                (row[0], float(row[1])) for row in self.connection.execute(gender_ratio).fetchall()
            ]

            # Save JSON report
            report_path = os.path.join(self.results_dir, "census_report.json")
            with open(report_path, "w") as f:
                json.dump(report, f)

            # Generate markdown report with plots
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

            # Generate population change plot
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
            plt.savefig(os.path.join(self.results_dir, 'pop_change_plot.png'))
            plt.close()

            # Save markdown report
            with open(os.path.join(self.results_dir, 'census_report.md'), 'w') as f:
                f.write(report_content)

            logger.info("Data loading and report generation completed successfully")
            return report_content
        except Exception as e:
            logger.error(f"Loading failed: {e}")
            raise

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

@app.post("/load")
async def load_data():
    try:
        db_path = os.getenv("DB_PATH", "/data/census.sqlite")
        transformed_data_path = os.getenv("TRANSFORMED_DATA_PATH", "/data/transformed_data.json")
        results_dir = os.getenv("RESULTS_DIR", "/results")
        
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            raise HTTPException(status_code=500, detail=f"Database file not found: {db_path}")
        if not os.path.exists(transformed_data_path):
            logger.error(f"Transformed data file not found: {transformed_data_path}")
            raise HTTPException(status_code=500, detail=f"Transformed data file not found: {transformed_data_path}")

        os.makedirs(results_dir, exist_ok=True)
        if not os.access(results_dir, os.W_OK):
            logger.error(f"No write permission for {results_dir}")
            raise HTTPException(status_code=500, detail=f"No write permission for {results_dir}")

        db_conn = DatabaseConnection(db_path)
        census, state_fact = db_conn.reflect_tables()
        
        with open(transformed_data_path, "r") as f:
            data = json.load(f)
            values_list = data.get("values_list", [])
            transformed_data = data.get("transformed_data", {})
        
        loader = DataLoader(db_conn.connection, census, state_fact, results_dir)
        report_content = loader.load_data(values_list, transformed_data)
        
        db_conn.close_connection()
        return {"status": "success", "message": "Data loaded and reports generated", "report": report_content}
    except Exception as e:
        logger.error(f"Load endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)