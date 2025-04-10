
# 🧮 Census ETL Pipeline

This project implements a complete ETL (Extract, Transform, Load) pipeline for analyzing U.S. Census data using Python, SQLAlchemy, Pandas, and Matplotlib. It connects to a SQLite database, performs data cleaning and transformation, updates the database, and generates a markdown report with visualizations.

---

To run the **ETL pipeline** framework you have set up, follow the steps below:

### **Prerequisites**
1. **Install Python**: Ensure you have Python 3.x installed on your machine. You can check by running:
   ```bash
   python --version
   ```

2. **Install Dependencies**: Ensure you have the required dependencies listed in the `requirements.txt` file installed. If you haven't created one yet, you can use the following commands to install them:
   ```bash
   pip install -r docs/requirements.txt
   ```

3. **Ensure Database and Data Files**: 
   - Ensure the database file (`census.sqlite`) exists in the correct directory (under `data/census.sqlite`).
   - Ensure the CSV file (`census.csv`) is present in the `data` folder with the required data format.

4. **Set up your project structure**: If you haven't already done so, make sure your directory structure is set up correctly. For example:
   ```
census-data-explorer/
├── src
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── transform.py
│   ├── load.py
│   └── visualization.py
├── tests
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_transform.py
│   ├── test_load.py
│   └── test_visualization.py
├── data
│   └── README.md
├── docs
│   ├── README.md
│   └── requirements.txt
├── main.py
└── LICENSE
   ```

### **Steps to Run the Framework**

1. **Activate Your Python Environment (Optional)**:
   It's a good practice to create a virtual environment for your project to manage dependencies.
   
   - To create a virtual environment, run:
     ```bash
     python -m venv venv
     ```
   - Activate the virtual environment:
     - **On Windows**:
       ```bash
       venv\Scripts\activate
       ```
     - **On macOS/Linux**:
       ```bash
       source venv/bin/activate
       ```

2. **Install Dependencies** (if not already done):
   If you haven't installed the required dependencies yet, run:
   ```bash
   pip install -r docs/requirements.txt
   ```

3. **Run the ETL Pipeline**:
   To execute the entire ETL pipeline, simply run the `main.py` script using Python. In your terminal, navigate to the root directory of your project and execute:
   ```bash
   python main.py
   ```

   This will:
   - Start the ETL pipeline.
   - Extract data from the `census.csv`.
   - Transform the data (process it and perform SQL queries).
   - Load the transformed data into the database.
   - Generate a markdown report (`census_report.md`) and a plot (`pop_change_plot.png`).
   - Save the output files in the `results/` directory.

4. **Check the Results**:
   After running the pipeline:
   - **Reports**: A markdown report will be generated as `census_report.md` in the `results/` directory.
   - **Plots**: A bar chart plot (`pop_change_plot.png`) showing the population change will be saved in the `results/` directory.

5. **Optional - Running Tests**:
   If you have created test cases in the `tests/` directory, you can run the tests to validate the code. If you are using `pytest`:
   ```bash
   pytest tests/
   ```

---

### **Summary**
- Ensure your project files are correctly set up (database, CSV file, code files).
- Install all necessary dependencies.
- Run the `main.py` script to execute the ETL pipeline.
- Check the `results/` directory for the generated report and plot.


## 📊 Sample Output

- Average age by gender
- Percentage of female population in each state
- Top 10 states with highest population growth
- Bar chart visualization of population change

---

## 🚨 Error Handling

- Graceful handling of:
  - Missing files
  - Invalid database connections
  - Data formatting errors

Logs are generated to help debug issues efficiently.
