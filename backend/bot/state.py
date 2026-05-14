from django.conf import settings
from redis import Redis


WAITING_FOR_INGREDIENTS = "waiting_for_ingredients"

STATE_TTL_SECONDS = 600


def get_redis_client():
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_user_state_key(user_id):
    return f"bot:user:{user_id}:state"


def set_user_state(user_id, state):
    redis_client = get_redis_client()
    redis_client.set(get_user_state_key(user_id), state, ex=STATE_TTL_SECONDS)


def get_user_state(user_id):
    redis_client = get_redis_client()
    return redis_client.get(get_user_state_key(user_id))


def clear_user_state(user_id):
    redis_client = get_redis_client()
    redis_client.delete(get_user_state_key(user_id))
