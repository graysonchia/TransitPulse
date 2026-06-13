# TransitPulse

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Airflow](https://img.shields.io/badge/Airflow-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)
![Prophet](https://img.shields.io/badge/Prophet-111827?style=for-the-badge&logo=meta&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)

TransitPulse is an end-to-end public transit analytics project for exploring rail ridership patterns in Kuala Lumpur. It extracts GTFS static data, loads a PostgreSQL star schema, generates synthetic ridership facts for analytics, trains a Prophet forecasting model, and serves live operational insights through a Streamlit and Plotly dashboard.

The project is designed as a GitHub portfolio piece that demonstrates data engineering, warehouse modeling, exploratory analysis, forecasting, and dashboard development in one cohesive workflow.

## Project Highlights

- GTFS static ingestion from Malaysia's open data API
- PostgreSQL star schema with date, time, route, stop, and ridership fact tables
- Batch fact seeding for large-scale dashboard testing
- Exploratory data analysis notebooks with exported PNG charts
- Prophet-based 90-day daily ridership forecasting
- Streamlit dashboard with live PostgreSQL queries and interactive Plotly charts

## Architecture

```text
                 +-------------------------------+
                 | Malaysia GTFS Static API       |
                 | rapid-rail-kl ZIP              |
                 +---------------+---------------+
                                 |
                                 v
                 +-------------------------------+
                 | Python ETL                     |
                 | pipeline/etl_gtfs.py           |
                 +---------------+---------------+
                                 |
                                 v
+-------------------+    +-------------------------------+
| Synthetic Seeder  |--->| PostgreSQL Data Warehouse      |
| seed_ridership.py |    | dim_date, dim_time, dim_route  |
+-------------------+    | dim_stop, fact_ridership       |
                         +---------------+---------------+
                                         |
             +---------------------------+---------------------------+
             |                           |                           |
             v                           v                           v
+------------------------+   +------------------------+   +------------------------+
| EDA Notebook           |   | Forecasting Notebook   |   | Streamlit Dashboard    |
| notebooks/01_eda.ipynb |   | notebooks/02_...ipynb  |   | dashboard/app.py       |
+-----------+------------+   +-----------+------------+   +-----------+------------+
            |                            |                            |
            v                            v                            v
+------------------------+   +------------------------+   +------------------------+
| PNG charts             |   | Prophet model          |   | Live Plotly visuals    |
| notebooks/charts/      |   | models/*.pkl           |   | Browser UI             |
+------------------------+   +------------------------+   +------------------------+
```

## Tech Stack

- **Python**: ETL, data generation, analysis, forecasting
- **PostgreSQL**: relational warehouse and analytical query layer
- **SQLAlchemy**: database connections and parameterized SQL execution
- **pandas**: GTFS parsing, aggregation, notebook analysis
- **Streamlit**: interactive dashboard application
- **Plotly**: dashboard charts, heatmaps, and stop map
- **Prophet**: 90-day ridership forecasting
- **Airflow**: intended orchestration layer for scheduled ETL workflows

## Repository Structure

```text
TransitPulse/
|-- dashboard/
|   `-- app.py
|-- models/
|   `-- prophet_ridership.pkl
|-- notebooks/
|   |-- 01_eda.ipynb
|   |-- 02_forecasting.ipynb
|   `-- charts/
|-- pipeline/
|   |-- etl_gtfs.py
|   `-- seed_ridership.py
|-- sql/
|   `-- schema.sql
|-- .env
|-- .gitignore
`-- README.md
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/TransitPulse.git
cd TransitPulse
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

On macOS or Linux:

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install pandas requests python-dotenv sqlalchemy psycopg2-binary streamlit plotly seaborn matplotlib prophet
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=transitpulse
DB_USER=postgres
DB_PASSWORD=your_password_here
```

### 5. Create the PostgreSQL schema

Create the database, then run:

```bash
psql -U postgres -d transitpulse -f sql/schema.sql
```

## Run the ETL

Load GTFS route and stop dimensions, then generate date and time dimensions:

```bash
python pipeline/etl_gtfs.py
```

Generate 500,000 synthetic ridership fact rows:

```bash
python pipeline/seed_ridership.py
```

## Run the Analysis Notebooks

EDA notebook:

```bash
jupyter notebook notebooks/01_eda.ipynb
```

Forecasting notebook:

```bash
jupyter notebook notebooks/02_forecasting.ipynb
```

The EDA notebook saves charts to `notebooks/charts/`. The forecasting notebook saves:

- `notebooks/charts/forecast.png`
- `models/prophet_ridership.pkl`

## Launch the Dashboard

```bash
streamlit run dashboard/app.py
```

Then open the local Streamlit URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Dashboard Features

- Date range, route, and route type filters
- KPI cards for total ridership, average delay, busiest stop, and busiest route
- Daily ridership trend line chart
- Ridership by route bar chart
- Hour vs weekday ridership heatmap
- Stop location map with bubble size based on ridership

## Screenshots

Add dashboard screenshots here after running the app.

```text
docs/screenshots/dashboard-overview.png
docs/screenshots/ridership-heatmap.png
docs/screenshots/stop-map.png
```

## Key Insights

The TransitPulse dashboard is built to reveal:

- **Peak-hour demand patterns**: identify morning and evening commute surges by hour and weekday.
- **Route-level performance**: compare total passenger volume across LRT, Monorail, KTM, BUS, and other route types.
- **Station demand hotspots**: locate the busiest stops and visually inspect ridership concentration on the map.
- **Delay exposure**: compare average delay by route to highlight service reliability concerns.
- **Temporal trends**: track whether daily ridership is growing, declining, or showing seasonal behavior.
- **Forecasted demand**: estimate the next 90 days of ridership to support capacity planning.

## Future Improvements

- Add Apache Airflow DAGs for scheduled ETL and model refreshes
- Replace synthetic ridership with validated production ridership data when available
- Add model evaluation metrics and forecast backtesting
- Add route-stop relationship enrichment for more precise map filtering
- Package dependencies in `requirements.txt` or `pyproject.toml`

## License

This project is intended for educational and portfolio use.
