from aiogram.fsm.storage.memory import MemoryStorage
from bot.config import settings
from bot.core.logger import logger

def get_fsm_storage():
    if settings.REDIS_URL:
        try:
            from aiogram.fsm.storage.redis import RedisStorage
            from redis.asyncio import Redis
            redis_client = Redis.from_url(settings.REDIS_URL)
            storage = RedisStorage(redis=redis_client)
            logger.info("Using Redis for FSM Storage.")
            return storage
        except Exception as e:
            logger.warning(f"Failed to connect to Redis ({e}). Falling back to MemoryStorage.")
            return MemoryStorage()
    else:
        logger.info("No REDIS_URL provided. Using MemoryStorage for FSM.")
        return MemoryStorage()

