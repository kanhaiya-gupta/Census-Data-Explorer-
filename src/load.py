# src/load.py
import os
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float, Boolean
from sqlalchemy import insert, update
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, connection, engine, results_dir):
        self.engine = engine
        self.connection = connection
        self.metadata = MetaData()  # Make sure to initialize metadata here
        self.results_dir = results_dir

    def load(self, transformed_data, values_list, census, state_fact):
        """Load phase: Store transformed data and generate report"""
        logger.info("Starting data loading")

        try:
            data = Table('data', self.metadata,
                          Column('name', String(255), unique=True),
                          Column('count', Integer(), default=1),
                          Column('amount', Float()),
                          Column('valid', Boolean(), default=False))
            self.metadata.create_all(self.engine, checkfirst=True)

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

            plt.figure(figsize=(10, 6))
            states = [row[0] for row in transformed_data['pop_change']]
            changes = [row[1] for row in transformed_data['pop_change']]
            plt.bar(states, changes)
            plt.xticks(rotation=45)
            plt.title('Top 10 States by Population Change')
            plt.xlabel('State')
            plt.ylabel('Population Change')
            plt.tight_layout()
            plt.savefig(f'{self.results_dir}/pop_change_plot.png')
            plt.close()

            logger.info("Data loading and report generation completed successfully")
            return report_content

        except Exception as e:
            logger.error(f"Loading failed: {e}")
            raise
