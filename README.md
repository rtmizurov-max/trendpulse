TrendPulse — Real-Time News Analytics Platform

Платформа аналитики новостей в реальном времени на основе Apache Kafka и ClickHouse. Полностью контейнеризована с Docker и Kubernetes.

Возможности

* Ingestion: Сбор данных с HackerNews API и RSS лент каждые 60 секунд
* Streaming: Буферизация и передача данных через Apache Kafka
* Storage: Запись в аналитическую БД ClickHouse с высокой скоростью агрегаций
* Orchestration: Ежедневные батчевые задачи через Apache Airflow
* Analytics: Готовые Grafana дашборды с топ постами и трендами
* Data Lake: Хранение сырых данных в MinIO (S3-совместимое хранилище)
* Infrastructure: Полная контейнеризация, запуск одной командой

Стек

* Apache Kafka — брокер сообщений, топики: hackernews-posts, rss-news, reddit-posts
* ClickHouse — аналитическая колоночная БД
* Apache Airflow — оркестрация батчевых задач
* Grafana — визуализация и дашборды
* MinIO — Data Lake, self-hosted аналог S3
* Kubernetes (k3s) — оркестрация Python приложений
* Docker Compose — управление инфраструктурой

Быстрый старт

Требования: Docker, k3s, Python 3.11+, kubectl

   git clone https://github.com/rtmizurov-max/trendpulse.git
   cd trendpulse
   chmod +x start.sh
   ./start.sh

Сервисы

   Kafka UI  — http://localhost:8080
   Grafana   — http://localhost:3000  (admin / trendpulse123)
   Airflow   — http://localhost:8082  (admin / admin)
   MinIO     — http://localhost:9001  (trendpulse / trendpulse123)

Пайплайн

   1. Producers опрашивают HackerNews API и RSS ленты каждые 60 секунд
   2. Данные отправляются в топики Kafka
   3. Consumer читает из Kafka и батчами пишет в ClickHouse
   4. Airflow каждую ночь агрегирует данные и дампит в MinIO
   5. Grafana визуализирует данные из ClickHouse в реальном времени

Структура проекта

   producers/          скрипты сбора данных
   consumer/           Kafka to ClickHouse consumer
   airflow/dags/       Airflow DAG
   kafka/              Docker Compose инфраструктура
   k8s/                Kubernetes манифесты
   grafana/            дашборд JSON
   clickhouse/config/  конфигурация ClickHouse
   Dockerfile          образ для Python приложений
   start.sh            запуск одной командой

Планы

   - Reddit API интеграция (ожидает одобрения заявки)
   - Дамп данных в MinIO через Airflow
   - Анализ тональности через HuggingFace
   - Helm charts для полного деплоя в Kubernetes
