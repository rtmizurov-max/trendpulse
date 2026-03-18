TrendPulse — Real-Time News Analytics Platform

Платформа аналитики новостей в реальном времени. Система собирает данные с HackerNews и RSS лент, передаёт их через Apache Kafka, обрабатывает Python Consumer и сохраняет в ClickHouse. Grafana визуализирует тренды в реальном времени. Airflow оркестрирует ежедневные батчевые задачи. Все приложения задеплоены в Kubernetes, инфраструктура управляется через Docker Compose.

ВОЗМОЖНОСТИ

Extract: Сбор данных с HackerNews API и RSS лент (BBC, NYT, HackerNews RSS) каждые 60 секунд с автоматическим retry при сбоях

Streaming: Буферизация и передача данных через Apache Kafka с тремя топиками и партиционированием

Load: Идемпотентная запись в ClickHouse батчами по 5 сообщений, колоночное хранение для быстрых агрегаций

Orchestration: Ежедневные батчевые задачи через Apache Airflow — агрегации, очистка старых данных, дамп в MinIO

Analytics: Готовые Grafana дашборды — топ постов по скору, активность по часам, топ авторов, распределение по источникам

Data Lake: Хранение сырых данных в MinIO — self-hosted S3-совместимое хранилище для переобработки

Infrastructure: Полная контейнеризация через Docker Compose и Kubernetes, запуск одной командой

ТЕХНОЛОГИЧЕСКИЙ СТЕК

Инфраструктура:
- Apache Kafka + Zookeeper — брокер сообщений, топики: hackernews-posts, rss-news, reddit-posts, 3 партиции на топик
- ClickHouse — аналитическая колоночная БД, движок MergeTree, оптимизирована для агрегаций
- Apache Airflow — оркестрация батчевых задач, DAG trendpulse_daily запускается каждую ночь в 00:00
- Grafana — визуализация данных из ClickHouse, плагин grafana-clickhouse-datasource
- MinIO — Data Lake, self-hosted аналог AWS S3, хранение сырых данных в JSON формате

Приложения и оркестрация:
- Kubernetes k3s — лёгкая версия Kubernetes для локального деплоя, оркестрирует producers и consumer
- Docker Compose — управляет инфраструктурными сервисами в единой Docker сети
- Python 3.11 — producers, consumer, Airflow DAG

АРХИТЕКТУРА

Инфраструктура (Docker Compose):
   Zookeeper → Kafka → Kafka UI
   ClickHouse
   MinIO
   Grafana
   Airflow

Приложения (Kubernetes):
   hackernews-producer — читает HackerNews API, пишет в Kafka
   rss-producer        — читает RSS ленты, пишет в Kafka
   reddit-producer     — читает Reddit API, пишет в Kafka (в разработке)
   consumer            — читает из Kafka, пишет в ClickHouse

ПАЙПЛАЙН ДАННЫХ

1. Producers каждые 60 секунд опрашивают HackerNews API и RSS ленты
2. Каждое сообщение сериализуется в JSON и отправляется в соответствующий Kafka топик
3. Consumer читает из топиков hackernews-posts и rss-news, накапливает батч из 5 сообщений
4. Батч вставляется в ClickHouse через HTTP интерфейс в формате TabSeparated
5. Airflow DAG каждую ночь считает агрегации, выбирает топ постов и чистит данные старше 30 дней
6. Grafana опрашивает ClickHouse и отображает актуальные данные на дашборде

БЫСТРЫЙ СТАРТ

Требования:
- Docker и Docker Compose
- k3s
- Python 3.11+
- kubectl
- Git

Установка зависимостей:

Docker:
   sudo dnf install -y docker git
   sudo systemctl enable --now docker
   sudo usermod -aG docker $USER
   newgrp docker

k3s:
   curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable traefik" sh -s - --write-kubeconfig-mode 644

kubectl конфиг:
   mkdir -p ~/.kube
   sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
   sudo chown $USER ~/.kube/config

Python зависимости:
   pip install kafka-python requests feedparser

Запуск проекта:

   git clone https://github.com/rtmizurov-max/trendpulse.git
   cd trendpulse
   chmod +x start.sh
   ./start.sh

СЕРВИСЫ ПОСЛЕ ЗАПУСКА

Kafka UI  — http://localhost:8080
Grafana   — http://localhost:3000  (admin / trendpulse123)
Airflow   — http://localhost:8082  (admin / admin)
MinIO     — http://localhost:9001  (trendpulse / trendpulse123)

СТРУКТУРА ПРОЕКТА

producers/
   hackernews_producer.py   сбор данных с HackerNews Firebase API
   rss_producer.py          парсинг RSS лент BBC, NYT, HackerNews
   reddit_producer.py       сбор данных с Reddit API (в разработке)

consumer/
   consumer.py              чтение из Kafka и запись в ClickHouse

airflow/
   dags/
      trendpulse_dag.py     DAG с задачами агрегации и очистки

kafka/
   docker-compose.yml       вся инфраструктура одним файлом

k8s/
   producers.yaml           Kubernetes Deployment манифесты

grafana/
   dashboard.json           экспорт дашборда для импорта

clickhouse/
   config/
      no-auth.xml           конфигурация пользователей ClickHouse

Dockerfile                  образ для Python приложений на python:3.11-slim
start.sh                    единая точка запуска всего проекта

AIRFLOW DAG

DAG trendpulse_daily содержит три задачи которые выполняются последовательно каждый день в полночь:

1. count_records      — подсчёт общего количества записей в ClickHouse
2. get_daily_top      — выборка топ-10 постов по скору за текущий день
3. cleanup_old_data   — удаление записей старше 30 дней

ПЛАНЫ ПО РАЗВИТИЮ

- Reddit API интеграция (ожидает одобрения заявки на developers.reddit.com)
- Дамп сырых данных в MinIO через Airflow с партиционированием по дате
- Анализ тональности заголовков через HuggingFace transformers
- Helm charts для полного деплоя всего стека в Kubernetes
- Sentiment дашборд в Grafana

Автор: rtmizurov-max
Лицензия: MIT
