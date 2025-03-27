import pathlib
import uvicorn
import logging
from fastapi import FastAPI, HTTPException, Request, Security, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt, ExpiredSignatureError
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from app import config
from app.database import init_db, close_db
from app.schemas import ChatResponse, ChatRequest
from app.utils import get_gigachat, get_trimmer, ask_gigachat, start_worker


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Логика при старте и завершении работы FastAPI"""
    await init_db()
    app.state.model = get_gigachat()
    app.state.trimmer = get_trimmer(app.state.model)
    await start_worker()

    yield

    await close_db()
    app.state.model = None
    app.state.trimmer = None


app = FastAPI(lifespan=lifespan)
security = HTTPBearer()


async def verify_jwt(token: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(token.credentials, config.JWT_SECRET, algorithms=["HS256"])
        exp = payload.get("exp")
        if exp is None:
            raise HTTPException(status_code=401, detail="Token missing expiration")

        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик ошибок"""
    logging.error(f'Ошибка: {exc}')
    return JSONResponse(
        status_code=500,
        content={'detail': f'Внутренняя ошибка сервера - {exc}'}
    )


@app.post(
    '/chat',
    response_model=ChatResponse,
    dependencies=[Depends(verify_jwt)],
    status_code=status.HTTP_200_OK,
    summary='Чат с GigaChat',
    description="""
    Основной эндпоинт для общения с GigaChat.
    Принимает сообщение пользователя и возвращает ответ ИИ с сохранением контекста.
    """,
    responses={
        200: {'description': 'Успешный ответ от GigaChat'},
        401: {'description': 'Невалидный или просроченный JWT токен'},
        500: {'description': 'Ошибка сервера при обработке запроса'}
    }
)
async def chat(request: ChatRequest):
    """Основной эндпоинт, для общения с Гигачатом"""
    model = app.state.model
    trimmer = app.state.trimmer

    try:
        ai_res = await ask_gigachat(request.user_id, request.message, model, trimmer)
        return ChatResponse(response=ai_res)
    except Exception as e:
        logging.error(f'Ошибка в обработке запроса: {e}')
        raise HTTPException(status_code=500, detail='Ошибка обработки запроса')


if __name__ == '__main__':
    cwd = pathlib.Path(__file__).parent.parent.resolve()
    log_config_path = f'{cwd}/log_config.ini'
    uvicorn.run('app.main:app', host="0.0.0.0", port=8000, reload=True, log_config=log_config_path)
