import os
import redis
from dotenv import load_dotenv

load_dotenv()

redis_client=redis.Redis.from_url(os.environ['REDIS_URL'], decode_responses=True, protocol=2)

def cache_get(key: str) -> str | None:
    try:
        return redis_client.get(key)
    except redis.RedisError:
        return None

def cache_set(key: str, value: str, seconds:int = 60)->None:
    try:
        redis_client.setex(key, seconds, value)
    except redis.RedisError:
        return None

def cache_delete_pattern(pattern: str)->None:
    try:
        for key in redis_client.scan_iter(pattern):
            redis_client.delete(key)
    except redis.RedisError:
        return None

