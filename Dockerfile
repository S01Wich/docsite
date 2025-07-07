FROM python:3.9-slim

# Prevents Python from writing pyc files to disc and buffer stdout/stderr
ENV PYTHONUNBUFFERED 1
# Set default Django settings module
ENV DJANGO_SETTINGS_MODULE=docsite.settings

WORKDIR /app

# Install system dependencies for building lxml and other packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libxml2-dev \
       libxslt1-dev \
       python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Collect static files (if using Django staticfiles)
RUN python manage.py collectstatic --no-input

# Expose the port the app runs on
EXPOSE 8000

# Launch the app with Gunicorn
CMD ["gunicorn", "docsite.wsgi:application", "--bind", "0.0.0.0:8000"]
