import requests
import json
import time
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def fetch_top_stories():
    ids = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json').json()
    return ids[:30]

def fetch_story(story_id):
    return requests.get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json').json()

print("HackerNews producer started...")

seen = set()
while True:
    story_ids = fetch_top_stories()
    for sid in story_ids:
        if sid not in seen:
            story = fetch_story(sid)
            if story and story.get('type') == 'story':
                producer.send('hackernews-posts', story)
                print(f"Sent: {story.get('title', 'no title')}")
                seen.add(sid)
    time.sleep(60)
