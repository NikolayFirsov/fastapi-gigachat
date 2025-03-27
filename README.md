# FastAPI GigaChat микросервис

Микросервис для интеграции с GigaChat API через REST интерфейс с сохранением контекста в PostgreSQL. 

## Быстрый старт
### Требования:
- Docker и Docker Compose
- API-токен GigaChat

1. Склонируйте репозиторий:
   ```bash
   git clone https://github.com/NikolayFirsov/fastapi-gigachat.git
   ````
   ```bash
   cd fastapi-gigachat
   ```
2. Создайте .env файл:
   ```bash
   cp .env.example .env
   ```
   
   Пример содержимого .env:
```dotenv
JWT_SECRET=a-very-very-secret-key-for-hs256-sig

DB_USER=appuser
DB_PASSWORD=strongpassword
DB_NAME=gigachat_db
DB_HOST=postgres
DB_PORT=5432

GIGA_TOKEN=your_token_here
GIGA_SCOPE=giga_scope
GIGA_MODEL=giga_model
MAX_TOKENS_FOR_TRIMMER=2500
```
3. Запустите сервисы:
   ```bash
   docker-compose up -d
   ```
   
## API Endpoints
Чат с GigaChat
```http
POST /chat
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
  "user_id": 123,
  "message": "Привет"
}
```
Пример ответа:
```json
{
  "response": "Привет! Как я могу помочь?"
}
```

## Документация API:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Устранение проблем
Если БД не инициализируется:
```bash
   docker-compose down -v  # Удаляет тома
   docker-compose up -d    # Полная пересборка
```
