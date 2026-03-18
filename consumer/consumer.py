from kafka import KafkaConsumer
import json
import requests
import threading
import os

KAFKA_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
CH_URL = os.getenv('CLICKHOUSE_URL', 'http://localhost:8123/')

def ch_insert(query, lines):
    body = query + '\n' + '\n'.join(lines)
    r = requests.post(CH_URL, data=body.encode('utf-8'))
    if r.status_code != 200:
        print(f"ClickHouse error: {r.text}")

def consume_hackernews():
    consumer = KafkaConsumer(
        'hackernews-posts',
        bootstrap_servers=KAFKA_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='trendpulse-hn-2'
    )
    print("[HackerNews] Consumer started!")
    buffer = []
    for msg in consumer:
        try:
            m = msg.value
            id_ = int(m.get('id', 0))
            title = str(m.get('title', '')).replace('\t','').replace('\n','')
            score = int(m.get('score', 0))
            url = str(m.get('url', '')).replace('\t','').replace('\n','')
            by = str(m.get('by', '')).replace('\t','').replace('\n','')
            time_ = int(m.get('time', 0))
            comments = int(m.get('descendants', 0))
            buffer.append(f"{id_}\t{title}\t{score}\t{url}\t{by}\t{time_}\t{comments}")
            if len(buffer) >= 5:
                ch_insert("INSERT INTO trendpulse.hackernews (id,title,score,url,by,time,num_comments) FORMAT TabSeparated", buffer)
                print(f"[HackerNews] Inserted {len(buffer)} rows")
                buffer = []
        except Exception as e:
            print(f"[HackerNews] Error: {e}")

def consume_rss():
    consumer = KafkaConsumer(
        'rss-news',
        bootstrap_servers=KAFKA_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='trendpulse-rss-2'
    )
    print("[RSS] Consumer started!")
    buffer = []
    for msg in consumer:
        try:
            m = msg.value
            title = str(m.get('title', '')).replace('\t','').replace('\n','')
            link = str(m.get('link', '')).replace('\t','').replace('\n','')
            summary = str(m.get('summary', ''))[:500].replace('\t','').replace('\n','')
            published = str(m.get('published', '')).replace('\t','').replace('\n','')
            source = str(m.get('source', '')).replace('\t','').replace('\n','')
            buffer.append(f"{title}\t{link}\t{summary}\t{published}\t{source}")
            if len(buffer) >= 5:
                ch_insert("INSERT INTO trendpulse.rss_news (title,link,summary,published,source) FORMAT TabSeparated", buffer)
                print(f"[RSS] Inserted {len(buffer)} rows")
                buffer = []
        except Exception as e:
            print(f"[RSS] Error: {e}")

t1 = threading.Thread(target=consume_hackernews)
t2 = threading.Thread(target=consume_rss)
t1.start()
t2.start()
t1.join()
t2.join()
