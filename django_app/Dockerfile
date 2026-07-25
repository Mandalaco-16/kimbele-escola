FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/staticfiles /app/mediafiles
EXPOSE 8000
CMD python manage.py makemigrations escola --noinput && python manage.py migrate --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
