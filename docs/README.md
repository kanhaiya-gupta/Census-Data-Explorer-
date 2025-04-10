# Census Data Explorer

A Python project to explore and analyze data from a PostgreSQL census database.

## Setup
1. Install dependencies: `pip install -r docs/requirements.txt`
2. Configure the database URL in `src/config.py`.
3. Run the app: `python main.py`

## Features
- Connect to a PostgreSQL database.
- Query and analyze census data.
- Visualize results (optional).



This ETL pipeline reorganization includes:

1. **Extract Phase**:
   - Connects to SQLite databases
   - Reflects existing tables
   - Reads data from CSV file
   - Verifies file existence

2. **Transform Phase**:
   - Calculates average age by gender
   - Computes percentage of women by state
   - Determines top 10 states by population change
   - Prepares CSV data for loading
   - Returns transformed data in a structured format

3. **Load Phase**:
   - Creates a new table for data storage
   - Loads CSV data into census table
   - Generates a report artifact with analysis results
   - Updates existing tables with new information

Key Features:
- Organized as a class for better structure and reusability
- Error handling with try/except blocks
- Proper resource management with connection closing
- Maintains original functionality while adding structure
- Generates an artifact with analysis results
- Follows the artifact tagging requirements
- Includes all necessary imports at the top

To use this pipeline:
1. Ensure the specified file paths exist
2. Make sure required libraries (pandas, sqlalchemy, matplotlib) are installed
3. Run the script, and it will execute the complete ETL process

The pipeline preserves the core functionality from your original code while providing a more structured and maintainable approach to data processing.
