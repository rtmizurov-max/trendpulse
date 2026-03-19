from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import requests

default_args = {
    'owner': 'trendpulse',
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

CH_URL = 'http://clickhouse:8123/'

def count_records():
    r = requests.get(CH_URL, params={'query': 'SELECT count() FROM trendpulse.hackernews'})
    print(f"Total HackerNews records: {r.text.strip()}")
    r2 = requests.get(CH_URL, params={'query': 'SELECT count() FROM trendpulse.rss_news'})
    print(f"Total RSS records: {r2.text.strip()}")

def get_daily_top():
    query = "SELECT title, score, by FROM trendpulse.hackernews ORDER BY score DESC LIMIT 10"
    r = requests.get(CH_URL, params={'query': query})
    print("=== TOP 10 ===")
    for row in r.text.strip().split('\n'):
        print(row)

def dump_to_minio():
    import subprocess
    from datetime import datetime
    date_str = datetime.now().strftime('%Y-%m-%d')

    # Получаем данные из ClickHouse
    r = requests.get(CH_URL, params={'query': 'SELECT * FROM trendpulse.hackernews FORMAT JSONEachRow'})
    with open(f'/tmp/hackernews_{date_str}.json', 'w') as f:
        f.write(r.text)

    r2 = requests.get(CH_URL, params={'query': 'SELECT * FROM trendpulse.rss_news FORMAT JSONEachRow'})
    with open(f'/tmp/rss_news_{date_str}.json', 'w') as f:
        f.write(r2.text)

    # Копируем в MinIO через mc
    setup = "mc alias set minio http://minio:9000 trendpulse trendpulse123"
    bucket = "mc mb --ignore-existing minio/trendpulse"
    cp1 = f"mc cp /tmp/hackernews_{date_str}.json minio/trendpulse/hackernews/{date_str}.json"
    cp2 = f"mc cp /tmp/rss_news_{date_str}.json minio/trendpulse/rss_news/{date_str}.json"

    for cmd in [setup, bucket, cp1, cp2]:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"CMD: {cmd}")
        print(f"OUT: {result.stdout}")
        print(f"ERR: {result.stderr}")

def cleanup_old_data():
    query = "ALTER TABLE trendpulse.hackernews DELETE WHERE toDateTime(time) < now() - INTERVAL 30 DAY"
    requests.post(CH_URL, data=query.encode())
    print("Cleanup done")

with DAG(
    'trendpulse_daily',
    default_args=default_args,
    description='TrendPulse daily pipeline',
    schedule_interval='0 0 * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False
) as dag:

    count = PythonOperator(task_id='count_records', python_callable=count_records)
    top_posts = PythonOperator(task_id='get_daily_top', python_callable=get_daily_top)
    dump = PythonOperator(task_id='dump_to_minio', python_callable=dump_to_minio)
    cleanup = PythonOperator(task_id='cleanup_old_data', python_callable=cleanup_old_data)

    count >> top_posts >> dump >> cleanup
