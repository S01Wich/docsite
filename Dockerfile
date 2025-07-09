FROM python:3.9-alpine

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=docsite.settings

WORKDIR /app

RUN apk update && apk add --no-cache \
    build-base \
    libxml2-dev libxslt-dev \
    libffi-dev openssl-dev \
    linux-headers \
    sqlite-dev sqlite

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/staticfiles

RUN python manage.py migrate --no-input \
    && python manage.py collectstatic --no-input

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]