#!/bin/bash
echo "Starting TrendPulse..."

sudo systemctl start docker
sudo systemctl start k3s
sleep 20

# SELinux контексты для всех монтируемых папок
sudo chcon -Rt svirt_sandbox_file_t ~/trendpulse/airflow/dags
sudo chcon -Rt svirt_sandbox_file_t ~/trendpulse/clickhouse/config
sudo chcon -Rt svirt_sandbox_file_t ~/trendpulse/grafana/provisioning

cd ~/trendpulse/kafka && docker compose up -d
echo "Waiting for infrastructure..."

until curl -s http://localhost:8123/ping > /dev/null 2>&1; do
    echo "Waiting for ClickHouse..."
    sleep 5
done
echo "ClickHouse is ready"

until docker exec kafka kafka-topics --list --bootstrap-server localhost:9092 > /dev/null 2>&1; do
    echo "Waiting for Kafka..."
    sleep 5
done
echo "Kafka is ready"

docker exec kafka kafka-topics --create --if-not-exists --bootstrap-server localhost:9092 --topic hackernews-posts --partitions 3 --replication-factor 1
docker exec kafka kafka-topics --create --if-not-exists --bootstrap-server localhost:9092 --topic rss-news --partitions 3 --replication-factor 1
docker exec kafka kafka-topics --create --if-not-exists --bootstrap-server localhost:9092 --topic reddit-posts --partitions 3 --replication-factor 1

docker exec clickhouse clickhouse-client --query "CREATE DATABASE IF NOT EXISTS trendpulse"
docker exec clickhouse clickhouse-client --query "CREATE TABLE IF NOT EXISTS trendpulse.hackernews (id UInt32, title String, score UInt32, url String, by String, time UInt32, num_comments UInt32, ingested_at DateTime DEFAULT now()) ENGINE = MergeTree() ORDER BY (time, id)"
docker exec clickhouse clickhouse-client --query "CREATE TABLE IF NOT EXISTS trendpulse.rss_news (title String, link String, summary String, published String, source String, ingested_at DateTime DEFAULT now()) ENGINE = MergeTree() ORDER BY (ingested_at, source)"

echo "Installing mc in Airflow..."
until docker exec airflow echo ok > /dev/null 2>&1; do
    echo "Waiting for Airflow..."
    sleep 5
done
docker exec -u root airflow bash -c "curl -o /usr/local/bin/mc https://dl.min.io/client/mc/release/linux-amd64/mc && chmod +x /usr/local/bin/mc"
echo "mc installed"

echo "Building Docker image..."
cd ~/trendpulse
docker build --network host -t trendpulse:latest .
docker save trendpulse:latest | sudo k3s ctr images import -

until kubectl get nodes > /dev/null 2>&1; do
    echo "Waiting for Kubernetes..."
    sleep 5
done
echo "Kubernetes is ready"

kubectl apply -f ~/trendpulse/k8s/producers.yaml

echo "TrendPulse is running!"
echo "Kafka UI  — http://localhost:8080"
echo "Grafana   — http://localhost:3000  (admin / trendpulse123)"
echo "Airflow   — http://localhost:8082  (admin / admin)"
echo "MinIO     — http://localhost:9001  (trendpulse / trendpulse123)"
