# main.py
import logging
import os
import pandas as pd
from src.database import DatabaseConnection
from src.transform import DataTransformer
from src.load import DataLoader
from src.visualization import Visualizer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Set base directory and paths
    base_dir = os.path.abspath(os.path.dirname(__file__))
    census_db_path = os.path.join(base_dir, 'data', 'census.sqlite')
    census_csv_path = os.path.join(base_dir, 'data', 'census.csv')
    results_dir = os.path.join(base_dir, 'results')

    # Create the necessary directories if they don't exist
    os.makedirs(results_dir, exist_ok=True)

    # Set up pipeline components
    db_conn = DatabaseConnection(census_db_path)
    census, state_fact = db_conn.reflect_tables()
    transformer = DataTransformer(db_conn.connection, census, state_fact)
    loader = DataLoader(db_conn.connection, db_conn.engine, results_dir)
    visualizer = Visualizer(results_dir)

    try:
        # Step 1: Extract data from the CSV
        logger.info("Starting data extraction from CSV")
        if not os.path.exists(census_csv_path):
            logger.error(f"CSV file not found at {census_csv_path}")
            raise FileNotFoundError(f"CSV file not found at {census_csv_path}")

        census_df = pd.read_csv(census_csv_path, header=None)
        census_df.columns = ['state', 'sex', 'age', 'pop2000', 'pop2008']
        logger.info(f"Successfully extracted {len(census_df)} records from CSV")

        # Step 2: Transform the extracted data
        logger.info("Starting data transformation")
        transformed_data, values_list = transformer.transform(census_df)

        # Step 3: Load the transformed data into the database and generate a report
        logger.info("Starting data loading and report generation")
        report_content = loader.load(transformed_data, values_list, census, state_fact)

        # Step 4: Visualize the population change data and save the plot
        logger.info("Generating population change plot")
        visualizer.plot_population_change(transformed_data['pop_change'])

        # Optional: Save the final report as a Markdown file
        report_path = os.path.join(results_dir, 'census_report.md')
        with open(report_path, 'w') as f:
            f.write(report_content)

        logger.info(f"ETL pipeline completed successfully. Report saved to {report_path}")

    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}")
        raise

    finally:
        # Close the database connection
        db_conn.close_connection()

if __name__ == "__main__":
    main()
