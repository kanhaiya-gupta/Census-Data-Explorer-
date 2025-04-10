# src/transform.py
import pandas as pd
import logging
from sqlalchemy import (
    String, Integer, Float, Boolean,
    select, func, case, cast, desc
)


logger = logging.getLogger(__name__)

class DataTransformer:
    def __init__(self, connection, census, state_fact):
        self.connection = connection
        self.census = census
        self.state_fact = state_fact

    def transform(self, census_df):
        """Transform phase: Process and analyze the extracted data"""
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

            transformed_data['avg_age'] = avg_age_results
            transformed_data['percent_female'] = percent_female_results
            transformed_data['pop_change'] = pop_change_results

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