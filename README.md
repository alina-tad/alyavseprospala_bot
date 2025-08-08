# Alyavseprospala Bot — LLM-ассистент для осмысления снов

## О проекте

Телеграм-бот помогает мягко осмыслять сны через уточняющие вопросы и авторский стиль интерпретаций. Не использует сонники, не даёт «гаданий», а ведёт к самостоятельным инсайтам.

- **Формат:** Telegram Bot (aiogram)
- **LLM:** через OpenRouter (primary + fallback-модели)
- **Данные/логи:** JSON файлы (KISS)
- **Запуск:** uv / Docker / Railway

## Быстрый старт (локально)

1. Установите uv и зависимости:
   ```
   uv sync --dev
   ```
2. Создайте `.env` в корне (примеры ключей ниже).
3. Запустите бота:
   ```
   uv run python main.py
   ```

### Переменные окружения (.env)
- `TELEGRAM_BOT_TOKEN` — токен бота
- `OPENROUTER_API_KEY` — ключ OpenRouter
- `LLM_PRIMARY_MODEL` — основная модель (например, `qwen/qwen3-8b` или `gpt-4`)
- `LLM_FALLBACK_MODELS` — резервные модели (через запятую), опц.
- `LLM_FALLBACK_ENABLED` — `true/false` (по умолчанию true)
- `LLM_MAX_TOKENS` — лимит токенов ответа (по умолчанию 1200)
- `LOG_LEVEL` — `DEBUG|INFO|WARNING|ERROR` (по умолчанию INFO)
- `ADMIN_USER_ID` — Telegram ID администратора (для /stats, /export, /clear)

## Запуск в Docker

- Собрать dev-образ и прогнать тесты в контейнере:
  ```
  make build-dev
  make test
  ```
- Прод-образ и запуск бота:
  ```
  make build
  make run
  # остановка
  make stop
  ```
Данные и логи будут в `./data` на хосте.

## Команды бота
- `/start` — приветствие и готовность помочь в интерпретации снов
- `/stop` — завершить диалог
- `/clear` — очистить историю (только админ)
- `/export` — экспорт истории (только админ)
- `/stats` — краткая статистика (только админ)

## Архитектура (KISS)
```
Пользователь → Telegram Bot → LLM Client → OpenRouter
                ↓
            Data Manager → JSON файлы
```
- Bot: aiogram, команды и обработка сообщений
- LLM Client: OpenRouter через OpenAI-совместимый клиент (primary + fallback)
- Data Manager: история, экспорт, статистика (JSON)
- Логирование/события: структурированный JSON (см. ниже)

## Логи и метрики
- `data/app.jsonl` — структурированные логи (INFO/WARNING/ERROR)
- `data/events.jsonl` — события (start, message_in/out, export, clear, stop)
- `data/metrics.json` — простые счётчики (requests/success/errors, timings, per model)

## Структура проекта (основное)
```
cursor_dreams_bot/
├── main.py
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── Makefile
├── prompts/
│   └── alyavseprospala_prompt.txt
├── src/
│   ├── __init__.py
│   ├── bot.py
│   ├── llm.py
│   ├── config.py
│   ├── data_manager.py
│   ├── logging_utils.py
│   └── metrics.py
├── tests/
│   └── ... (минимальные тесты критичного функционала)
├── data/ (runtime)
└── doc/
    ├── product_idea.md
    ├── vision.md
    ├── tasklist.md
    ├── llm_doc.md
    └── guides/
        └── cloud_deploy.md
```

## Облачный деплой (Railway)
- Подробный гайд: `doc/guides/cloud_deploy.md`
- Коротко: подключить репозиторий GitHub → обнаружится Dockerfile → задать Variables (`TELEGRAM_BOT_TOKEN`, `OPENROUTER_API_KEY`, и т.д.) → Deploy → в логах увидеть `Start polling`.

## Сценарий работы (MVP)
1) Пользователь описывает сон → бот задаёт уточняющие вопросы.
2) Бот даёт интерпретацию в авторском стиле (без «сонников»).
3) Администратор может выгрузить историю и посмотреть статистику.

## Документы
- Идея продукта: `doc/product_idea.md`
- Техническое видение: `doc/vision.md`
- План итераций: `doc/tasklist.md`
- LLM (primary/fallback): `doc/llm_doc.md`
- Облачное развертывание (Railway): `doc/guides/cloud_deploy.md`

## Тесты
- Локально: `uv run pytest -q`
- В контейнере: `make build-dev && make test`

---
Сделано по принципам KISS и MVP: минимум зависимостей, максимум пользы. 