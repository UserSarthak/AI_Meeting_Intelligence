import json

from redis_client import redis_client


def set_value(key, value):
    redis_client.set(key, value)


def get_value(key):
    return redis_client.get(key)


def delete_value(key):
    redis_client.delete(key)


def set_json(key, value, expire=600):
    redis_client.set(
        key,
        json.dumps(value, default=str),
        ex=expire
    )


def get_json(key):
    value = redis_client.get(key)

    if value is None:
        return None

    return json.loads(value)

def delete_meeting_cache(meeting_id):
    key = f"meeting:{meeting_id}"
    delete_value(key)

def delete_action_items_cache(meeting_id):
    key = f"meeting:{meeting_id}:action_items"
    delete_value(key)

    
