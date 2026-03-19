import feedparser
import json
import time
import os
from kafka import KafkaProducer

KAFKA_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

RSS_FEEDS = [
    'https://feeds.bbci.co.uk/news/rss.xml',
    'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
    'https://hnrss.org/frontpage',
]

seen = set()
print("RSS producer started...")

while True:
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            link = entry.get('link', '')
            if link not in seen:
                msg = {
                    'title': entry.get('title', ''),
                    'link': link,
                    'summary': entry.get('summary', ''),
                    'published': entry.get('published', ''),
                    'source': feed.feed.get('title', url)
                }
                producer.send('rss-news', msg)
                print(f"Sent: {msg['title'][:60]}")
                seen.add(link)
    time.sleep(300)
