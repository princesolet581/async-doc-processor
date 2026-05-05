import os
import redis
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def publish_event(job_id: str, status: str, event_name: str, message: str = ""):
    event_data = {
        "job_id": job_id,
        "status": status,
        "event_name": event_name,
        "message": message
    }
    redis_client.publish(f"job_progress_{job_id}", json.dumps(event_data))
