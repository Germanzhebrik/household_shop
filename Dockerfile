# Используем официальный легкий образ Python
FROM python:3.10-slim

# Устанавливаем переменные окружения, чтобы Python не кешировал файлы и сразу выводил логи
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем системные зависимости для работы с PostgreSQL и Pillow
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . /app/

# Открываем порт 8000
EXPOSE 8000

# Команда для запуска (используем gunicorn для продакшн-подобной среды или python manage.py для тестов)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]