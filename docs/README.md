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




This complete implementation includes:

1. **Full Features**:
   - Comprehensive error handling with try/except blocks
   - Detailed logging throughout the pipeline
   - Proper type conversion for database insertion
   - Visualization generation using matplotlib
   - Complete artifact generation with analysis results

2. **Extract Phase**:
   - Validates file existence
   - Reflects database tables
   - Loads CSV data with proper column names
   - Returns pandas DataFrame

3. **Transform Phase**:
   - Performs three key analyses:
     - Average age by gender
     - Percentage female by state
     - Top 10 states by population change
   - Converts DataFrame to list of dictionaries with proper typing
   - Returns both analysis results and prepared data

4. **Load Phase**:
   - Creates new table if needed
   - Inserts CSV data into census table
   - Updates state_fact table
   - Generates detailed report with formatted results
   - Creates visualization of population changes
   - Produces properly formatted artifact

5. **Execution**:
   - Runs all phases in sequence
   - Manages database connection lifecycle
   - Provides detailed logging output

To run this code:
1. Ensure all dependencies are installed (pandas, sqlalchemy, matplotlib)
2. Verify the file paths exist and are accessible
3. Execute the script directly

The code will:
- Log all operations
- Generate a population change plot (pop_change_plot.png)
- Create an artifact with the analysis report
- Handle any errors gracefully
- Clean up resources properly

The artifact contains a comprehensive report with all analysis results formatted in markdown, meeting the specified requirements for the xaiArtifact tag structure.
