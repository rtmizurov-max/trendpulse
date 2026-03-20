# TRENDPULSE — REAL-TIME NEWS ANALYTICS PLATFORM

**Платформа аналитики новостей в реальном времени**

TrendPulse — это полноценный Data Engineering проект, который собирает данные с HackerNews и RSS лент, передаёт их через Apache Kafka, обрабатывает Python Consumer и сохраняет в ClickHouse. Grafana визуализирует тренды в реальном времени, Airflow оркестрирует ежедневные батчевые задачи, а Kubernetes управляет приложениями. Вся инфраструктура поднимается одной командой.

---

## Содержание

- [Архитектура](#архитектура)
- [Стек технологий](#стек-технологий)
- [Структура проекта](#структура-проекта)
- [Пайплайн данных](#пайплайн-данных)
- [Быстрый старт](#быстрый-старт)
- [Сервисы](#сервисы)
- [Airflow DAG](#airflow-dag)
- [Kubernetes](#kubernetes)
- [Планы](#планы)

---

## Архитектура
```
┌─────────────────────────────────────────────────────────────┐
│                     ИСТОЧНИКИ ДАННЫХ                         │
│  HackerNews API    RSS Feeds (BBC, NYT)    Reddit API        │
└────────────┬───────────────┬───────────────────┬────────────┘
             │               │                   │
             ▼               ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                      APACHE KAFKA                            │
│   hackernews-posts    rss-news    reddit-posts               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    PYTHON CONSUMER                           │
│         Читает из Kafka, пишет в ClickHouse                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
┌────────────────────┐     ┌──────────────────────┐
│    CLICKHOUSE      │     │        MINIO          │
│  Аналитическая БД  │     │      Data Lake        │
└────────┬───────────┘     └──────────────────────┘
         │
         ▼
┌─────────────────────┐
│      GRAFANA        │
│  Дашборды и тренды  │
└─────────────────────┘

AIRFLOW    — батчевые задачи каждую ночь в 00:00
KUBERNETES — оркестрация producers и consumer
DOCKER     — управление инфраструктурой
```

---

## Стек технологий

| Компонент | Инструмент | Версия | Роль |
|-----------|-----------|--------|------|
| Брокер сообщений | Apache Kafka | 7.5.0 | Приём и хранение потока данных |
| Координатор | Zookeeper | 7.5.0 | Управление кластером Kafka |
| База данных | ClickHouse | latest | Аналитическое хранилище |
| Оркестрация задач | Apache Airflow | 2.8.0 | Батчевые задачи по расписанию |
| Визуализация | Grafana | latest | Дашборды в реальном времени |
| Data Lake | MinIO | latest | S3-совместимое хранилище |
| Контейнеры | Docker Compose | v2 | Управление инфраструктурой |
| Kubernetes | k3s | v1.28.5 | Оркестрация приложений |
| Язык | Python | 3.11 | Producers, Consumer, DAG |

---

## Структура проекта
```
trendpulse/
│
├── producers/
│   ├── hackernews_producer.py   # Сбор данных с HackerNews Firebase API
│   ├── rss_producer.py          # Парсинг RSS лент BBC, NYT, HackerNews
│   └── reddit_producer.py       # Сбор данных с Reddit API (в разработке)
│
├── consumer/
│   └── consumer.py              # Чтение из Kafka, запись в ClickHouse
│
├── airflow/
│   └── dags/
│       └── trendpulse_dag.py    # DAG с 4 задачами
│
├── kafka/
│   └── docker-compose.yml       # Вся инфраструктура одним файлом
│
├── k8s/
│   └── producers.yaml           # Kubernetes Deployment манифесты
│
├── grafana/
│   ├── dashboard.json           # Экспорт дашборда (импортируется автоматически)
│   └── provisioning/
│       ├── datasources/
│       │   └── clickhouse.yaml  # Автоматическое подключение ClickHouse
│       └── dashboards/
│           └── dashboards.yaml  # Автоматический импорт дашбордов
│
├── clickhouse/
│   └── config/
│       └── no-auth.xml          # Конфигурация пользователей ClickHouse
│
├── Dockerfile                   # Образ для Python приложений (python:3.11-slim)
├── start.sh                     # Единая точка запуска всего проекта
└── README.md
```

---

## Пайплайн данных
```
1. INGESTION
   Producers запускаются в Kubernetes и каждые 60 секунд опрашивают:
   - HackerNews Firebase API → топ 30 постов
   - RSS ленты BBC, NYT, HackerNews → новые статьи каждые 5 минут

2. STREAMING
   Каждое сообщение сериализуется в JSON и отправляется в Kafka топик:
   - hackernews-posts (3 партиции)
   - rss-news (3 партиции)

3. PROCESSING
   Python Consumer читает из Kafka и накапливает батч из 5 сообщений.
   Батч вставляется в ClickHouse через HTTP интерфейс в формате TabSeparated.

4. ORCHESTRATION
   Airflow DAG запускается каждую ночь в 00:00 и выполняет:
   - Подсчёт записей в базе
   - Выборку топ-10 постов за день
   - Дамп данных в MinIO (Data Lake)
   - Очистку записей старше 30 дней

5. VISUALIZATION
   Grafana подключается к ClickHouse и отображает:
   - Топ постов по скору
   - Активность по часам
   - Топ авторов
   - Распределение по источникам
```

---

## Быстрый старт

### Требования

- Fedora / RHEL / CentOS (или любой Linux с systemd)
- Docker и Docker Compose v2
- k3s (Kubernetes)
- kubectl
- Python 3.11+
- 4GB RAM минимум

### Установка зависимостей
```bash
# Docker
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker

# k3s
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable traefik" sh -s - --write-kubeconfig-mode 644

# kubectl настройка
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER ~/.kube/config

# SELinux бинарник k3s
sudo chcon -t bin_t /usr/local/bin/k3s

# k3s как системный сервис
sudo systemctl enable k3s
```

### Запуск
```bash
git clone https://github.com/rtmizurov-max/trendpulse.git
cd trendpulse
chmod +x start.sh
./start.sh
```

Скрипт автоматически:
- Запускает Docker и k3s
- Применяет SELinux контексты
- Поднимает все контейнеры через Docker Compose
- Ждёт готовности ClickHouse и Kafka
- Создаёт топики и таблицы
- Собирает Docker образ и импортирует в k3s
- Деплоит приложения в Kubernetes

### Остановка
```bash
kubectl delete -f ~/trendpulse/k8s/producers.yaml
sudo systemctl stop k3s
cd ~/trendpulse/kafka && docker compose down
```

---

## Сервисы

| Сервис | URL | Логин | Пароль |
|--------|-----|-------|--------|
| Kafka UI | http://localhost:8080 | — | — |
| Grafana | http://localhost:3000 | admin | trendpulse123 |
| Airflow | http://localhost:8082 | admin | admin |
| MinIO | http://localhost:9001 | trendpulse | trendpulse123 |

Grafana автоматически подключается к ClickHouse и импортирует дашборд при первом запуске.

---

## Airflow DAG

DAG `trendpulse_daily` содержит 4 задачи которые выполняются последовательно каждый день в полночь:
```
count_records → get_daily_top → dump_to_minio → cleanup_old_data
```

- `count_records` — подсчёт общего количества записей в ClickHouse
- `get_daily_top` — выборка топ-10 постов по скору за текущий день
- `dump_to_minio` — дамп таблиц hackernews и rss_news в MinIO в формате JSON с партиционированием по дате
- `cleanup_old_data` — удаление записей старше 30 дней

---

## Kubernetes

Приложения задеплоены в k3s через Deployment манифесты:

- `hackernews-producer` — 1 реплика, читает HackerNews API
- `rss-producer` — 1 реплика, парсит RSS ленты
- `consumer` — 1 реплика, читает Kafka и пишет в ClickHouse

Все поды используют `hostNetwork: true` для доступа к Kafka на хосте. При падении пода Kubernetes автоматически его перезапускает.

---

## Планы

- Reddit API интеграция (ожидает одобрения заявки на developers.reddit.com)
- Анализ тональности заголовков через HuggingFace transformers
- Helm charts для полного деплоя всего стека в Kubernetes
- Sentiment дашборд в Grafana
- Поддержка Ubuntu/Debian в start.sh
