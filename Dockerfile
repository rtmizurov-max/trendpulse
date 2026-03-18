FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    kafka-python \
    requests \
    feedparser \
    -i https://mirrors.aliyun.com/pypi/simple/

COPY producers/ ./producers/
COPY consumer/ ./consumer/
