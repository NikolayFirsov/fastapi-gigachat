import asyncio
import logging

from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_core.messages import trim_messages
from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app import config
from app.database import get_history, update_history


queue = None
semaphore = None


def get_gigachat():
    """Инициализация Гигачата"""
    model = GigaChat(
        credentials=config.GIGA_TOKEN,
        scope=config.GIGA_SCOPE,
        model=config.GIGA_MODEL,
        verify_ssl_certs=False,
    )
    return model


def get_trimmer(model):
    """Инициализация триммера для обрезки истории диалога"""
    trimmer = trim_messages(
        max_tokens=config.MAX_TOKENS_FOR_TRIMMER,
        strategy='last',
        token_counter=model,
        include_system=True,
        allow_partial=False,
        start_on='human',
    )
    return trimmer


async def worker():
    while True:
        user_id, user_input, model, trimmer, future = await queue.get()
        async with semaphore:
            try:
                result = await _ask_gigachat(user_id, user_input, model, trimmer)
                future.set_result(result)
            except Exception as e:
                logging.error(f'Ошибка в воркере: {e}')
                future.set_exception(e)
        queue.task_done()


async def start_worker():
    """Запускаем очередь и воркеры"""
    global queue, semaphore
    if queue is None:
        queue = asyncio.Queue()
    if semaphore is None:
        semaphore = asyncio.Semaphore(10)

    for _ in range(10):
        asyncio.create_task(worker())


@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
async def _ask_gigachat(user_id: int, user_input: str, model: GigaChat, trimmer: trim_messages):
    """Отправка запроса в ГигаЧат с ретраями на случай 429 ошибки"""
    user_sessions = await get_history(user_id)

    if not user_sessions:
        prompt = await read_prompt()
        user_sessions = [SystemMessage(content=prompt)]
    user_sessions.append(HumanMessage(content=user_input))

    try:
        res = await model.ainvoke(user_sessions)
    except Exception as e:
        logging.error(f'Ошибка при запросе к ГигаЧату: {e}')
        raise

    user_sessions.append(AIMessage(content=res.content))
    trim_sessions = await trimmer.ainvoke(user_sessions)
    await update_history(user_id, trim_sessions)

    return res.content


async def ask_gigachat(user_id: int, user_input: str, model: GigaChat, trimmer: trim_messages):
    """Добавление запроса в очередь и ожидание ответа"""
    if queue is None:
        raise RuntimeError('Очередь запросов не инициализирована! Запустите start_worker() в lifespan')

    future = asyncio.get_event_loop().create_future()
    await queue.put((user_id, user_input, model, trimmer, future))
    return await future


async def read_prompt():
    """Чтение промта из файла"""
    try:
        with open(config.PROMPT_FILE_PATH, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logging.error(f"Файл {config.PROMPT_FILE_PATH} не найден. Создаю новый файл со стандартным промтом.")
        with open(config.PROMPT_FILE_PATH, 'w', encoding='utf-8') as file:
            file.write(config.DEFAULT_PROMPT)
        return config.DEFAULT_PROMPT