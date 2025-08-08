FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Установка curl для установки uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Установка uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Кэшируем зависимости
COPY pyproject.toml uv.lock ./
# Опциональная установка dev-зависимостей для тестов в контейнере
ARG INSTALL_DEV=false
RUN if [ "$INSTALL_DEV" = "true" ]; then \
      uv sync --frozen --dev ; \
    else \
      uv sync --frozen --no-dev ; \
    fi

# Копируем исходники
COPY main.py ./
COPY src ./src
COPY prompts ./prompts
# Создаем каталог данных
RUN mkdir -p /app/data

# Запуск приложения
CMD ["uv", "run", "python", "main.py"]
