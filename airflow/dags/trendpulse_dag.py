from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests

default_args = {
    'owner': 'trendpulse',
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

CH_URL = 'http://clickhouse:8123/'

def get_daily_top():
    query = """
    SELECT title, score, by
    FROM trendpulse.hackernews
    ORDER BY score DESC
    LIMIT 10
    """
    r = requests.get(CH_URL, params={'query': query})
    print("=== TOP 10 TODAY ===")
    for row in r.text.strip().split('\n'):
        print(row)

def count_records():
    r = requests.get(CH_URL, params={'query': 'SELECT count() FROM trendpulse.hackernews'})
    print(f"Total records in ClickHouse: {r.text.strip()}")

def cleanup_old_data():
    query = "ALTER TABLE trendpulse.hackernews DELETE WHERE toDateTime(time) < now() - INTERVAL 30 DAY"
    r = requests.post(CH_URL, data=query.encode())
    print(f"Cleanup done: {r.status_code}")

with DAG(
    'trendpulse_daily',
    default_args=default_args,
    description='TrendPulse daily pipeline',
    schedule_interval='0 0 * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False
) as dag:

    count = PythonOperator(
        task_id='count_records',
        python_callable=count_records
    )

    top_posts = PythonOperator(
        task_id='get_daily_top',
        python_callable=get_daily_top
    )

    cleanup = PythonOperator(
        task_id='cleanup_old_data',
        python_callable=cleanup_old_data
    )

    count >> top_posts >> cleanup
