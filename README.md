TrendPulse — Платформа аналитики новостей в реальном времени

Проект по направлению Data Engineering. Система собирает данные с HackerNews и RSS лент, обрабатывает их в реальном времени и визуализирует тренды на дашборде.


АРХИТЕКТУРА

HackerNews API и RSS ленты отправляют данные в Apache Kafka. Python Consumer читает из Kafka и записывает в ClickHouse. Grafana визуализирует данные из ClickHouse. Airflow каждую ночь запускает батчевые задачи. MinIO хранит сырые данные как Data Lake. Kubernetes управляет Python приложениями. Docker Compose управляет инфраструктурой.


СТЕК ТЕХНОЛОГИЙ

1. Apache Kafka
   Брокер сообщений. Принимает данные от producers и хранит их в топиках до обработки.
   Выступает буфером между источниками данных и хранилищем.
   Топики: hackernews-posts, rss-news, reddit-posts.

2. Python Producers
   Скрипты которые каждые 60 секунд опрашивают внешние API и отправляют данные в Kafka.
   Источники: HackerNews API, RSS ленты (BBC, NYT, HackerNews RSS), Reddit API.

3. Python Consumer
   Читает сообщения из Kafka и батчами записывает в ClickHouse.
   Работает непрерывно как отдельный процесс.

4. ClickHouse
   Аналитическая колоночная база данных.
   Хранит все обработанные данные, оптимизирована для быстрых агрегаций.

5. Apache Airflow
   Оркестратор батчевых задач. DAG trendpulse_daily запускается каждый день в полночь.
   Задачи: подсчёт записей, выборка топ-10 постов за день, очистка данных старше 30 дней.

6. Grafana
   Визуализация данных из ClickHouse в реальном времени.
   Дашборды: топ постов по скору, активность по времени, топ авторов, источники новостей.

7. MinIO
   Self-hosted хранилище объектов, аналог S3. Data Lake для хранения сырых данных в JSON.

8. Kubernetes (k3s)
   Оркестрирует Python приложения (producers и consumer).
   Следит за работой подов и перезапускает их при падении.

9. Docker Compose
   Управляет инфраструктурными сервисами: Kafka, ClickHouse, MinIO, Grafana, Airflow.
   Все сервисы работают в одной Docker сети.


БЫСТРЫЙ СТАРТ

Требования:
   - Docker и Docker Compose
   - k3s
   - Python 3.11+
   - kubectl

Установка зависимостей:

   sudo dnf install -y docker
   sudo systemctl enable --now docker
   sudo usermod -aG docker $USER
   curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable traefik" sh -s - --write-kubeconfig-mode 644
   pip install kafka-python requests feedparser

Запуск:

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

   producers/          скрипты сбора данных с HackerNews, RSS, Reddit
   consumer/           Kafka to ClickHouse consumer
   airflow/dags/       Airflow DAG определения
   kafka/              Docker Compose для всей инфраструктуры
   k8s/                Kubernetes манифесты
   grafana/            экспорт дашборда Grafana
   clickhouse/config/  конфигурация ClickHouse
   Dockerfile          образ для Python приложений
   start.sh            запуск одной командой


ПАЙПЛАЙН ДАННЫХ

   1. Producers каждые 60 секунд опрашивают HackerNews API и RSS ленты
   2. Данные отправляются в соответствующие топики Kafka
   3. Consumer читает из Kafka и батчами записывает в ClickHouse
   4. Airflow каждую ночь агрегирует данные и делает дамп в MinIO
   5. Grafana в реальном времени визуализирует данные из ClickHouse


ПЛАНЫ ПО РАЗВИТИЮ

   - Интеграция с Reddit API (ожидает одобрения заявки)
   - Дамп данных в MinIO через Airflow
   - Анализ тональности текста через HuggingFace
   - Helm charts для полного деплоя в Kubernetes
