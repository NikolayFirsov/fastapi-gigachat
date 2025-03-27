import json
import asyncpg
from langchain_core.messages import messages_from_dict, message_to_dict

from app import config


pool = None


async def get_pool():
    global pool
    if pool is None:
        raise RuntimeError('База данных не инициализирована. Проверьте lifespan в main.py')
    return pool


async def init_db():
    """Инициализация пула соединений с БД"""
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            host=config.DB_HOST,
            port=config.DB_PORT
        )


async def close_db():
    """Закрытие пула соединений"""
    global pool
    if pool is not None:
        await pool.close()
        pool = None


async def get_history(user_id: int):
    """Получает историю сообщений пользователя из бд"""
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        query = """
        SELECT history 
        FROM user_sessions 
        WHERE user_id = $1
        """
        history = await conn.fetchval(query, user_id)
        return messages_from_dict(json.loads(history)) if history else []


async def update_history(user_id: int, history: list):
    """Обновляет историю сообщений пользователя в бд"""
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        query = """
        INSERT INTO user_sessions (user_id, history) 
        VALUES ($1, $2) 
        ON CONFLICT (user_id) DO UPDATE SET history = $2
        """
        json_history = json.dumps([message_to_dict(item) for item in history], ensure_ascii=False)
        await conn.execute(query, user_id, json_history)
