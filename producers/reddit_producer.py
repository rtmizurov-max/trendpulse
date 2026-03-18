import praw
import json
import time
from kafka import KafkaProducer

# Сюда вставишь свои ключи
reddit = praw.Reddit(
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    user_agent='trendpulse:v1.0'
)

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

SUBREDDITS = ['technology', 'worldnews', 'programming', 'datascience']

print("Reddit producer started...")

seen = set()
while True:
    for sub in SUBREDDITS:
        for post in reddit.subreddit(sub).hot(limit=25):
            if post.id not in seen:
                msg = {
                    'id': post.id,
                    'title': post.title,
                    'score': post.score,
                    'url': post.url,
                    'subreddit': sub,
                    'created_utc': post.created_utc,
                    'num_comments': post.num_comments
                }
                producer.send('reddit-posts', msg)
                print(f"Sent: {post.title[:60]}")
                seen.add(post.id)
    time.sleep(60)
