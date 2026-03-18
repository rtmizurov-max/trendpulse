#!/bin/bash
echo "Starting TrendPulse..."

sudo systemctl start docker
sudo systemctl start k3s
sleep 30

cd ~/trendpulse/kafka && docker compose up -d
echo "Waiting for infrastructure (30s)..."
sleep 30

# Топики
docker exec kafka kafka-topics --create --if-not-exists --bootstrap-server localhost:9092 --topic hackernews-posts --partitions 3 --replication-factor 1
docker exec kafka kafka-topics --create --if-not-exists --bootstrap-server localhost:9092 --topic rss-news --partitions 3 --replication-factor 1
docker exec kafka kafka-topics --create --if-not-exists --bootstrap-server localhost:9092 --topic reddit-posts --partitions 3 --replication-factor 1

# Таблицы ClickHouse
docker exec clickhouse clickhouse-client --query "CREATE DATABASE IF NOT EXISTS trendpulse"
docker exec clickhouse clickhouse-client --query "CREATE TABLE IF NOT EXISTS trendpulse.hackernews (id UInt32, title String, score UInt32, url String, by String, time UInt32, num_comments UInt32, ingested_at DateTime DEFAULT now()) ENGINE = MergeTree() ORDER BY (time, id)"
docker exec clickhouse clickhouse-client --query "CREATE TABLE IF NOT EXISTS trendpulse.rss_news (title String, link String, summary String, published String, source String, ingested_at DateTime DEFAULT now()) ENGINE = MergeTree() ORDER BY (ingested_at, source)"

# SELinux для airflow dags
sudo chcon -Rt svirt_sandbox_file_t ~/trendpulse/airflow/dags

# Деплоим в Kubernetes
KAFKA_IP=$(docker inspect kafka --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
sed -i "s/172\.[0-9]*\.[0-9]*\.[0-9]*/$KAFKA_IP/g" ~/trendpulse/k8s/producers.yaml
kubectl apply -f ~/trendpulse/k8s/producers.yaml

echo "TrendPulse is running!"
echo "Kafka UI:  http://localhost:8080"
echo "Grafana:   http://localhost:3000 (admin/trendpulse123)"
echo "Airflow:   http://localhost:8082 (admin/admin)"
echo "MinIO:     http://localhost:9001 (trendpulse/trendpulse123)"
