
# 🧮 Census ETL Pipeline

This project implements a complete ETL (Extract, Transform, Load) pipeline for analyzing U.S. Census data using Python, SQLAlchemy, Pandas, and Matplotlib. It connects to a SQLite database, performs data cleaning and transformation, updates the database, and generates a markdown report with visualizations.

---

## 📁 Project Structure

```
.
.
├── src/
│   ├── __init__.py             # Init for package
│   ├── config.py               # DB configuration
│   ├── database.py             # Connection logic
│   ├── analysis.py             # Data processing/transform logic
│   └── visualization.py        # Charting and plotting
├── tests/
│   ├── __init__.py
│   ├── test_database.py        # Unit tests for DB connection
│   └── test_analysis.py        # Unit tests for analysis
├── data/
│   └── README.md               # Notes on data format & usage
├── docs/
│   ├── README.md               # Project overview
│   └── requirements.txt        # Dependencies
├── main.py                     # Entry point for running the pipeline
├── .gitignore
├── LICENSE
└── README.md                   
```

---

## ⚙️ Features

- **Extract:** Loads data from a SQLite database and CSV file.
- **Transform:** Performs calculations including:
  - Average age by gender
  - Percentage of female population by state
  - Top 10 states by population change
- **Load:**
  - Inserts transformed data back into the database
  - Updates specific fields
  - Generates a markdown report
  - Creates a bar chart visualization

---

## 🛠️ Technologies Used

- Python 3.x
- Pandas
- SQLAlchemy
- SQLite
- Matplotlib
- Logging

---

## 🧪 How to Run

1. **Install dependencies:**

   ```bash
   pip install pandas sqlalchemy matplotlib
   ```

2. **Prepare the data:**
   - Place `census.csv` and `census.sqlite` inside the `data/` directory.

3. **Run the pipeline:**

   ```bash
   python etl_pipeline.py
   ```

4. **Output:**
   - `census_report.md`: Markdown report with insights
   - `pop_change_plot.png`: Chart showing top states by population change

---

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
