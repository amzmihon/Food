FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=meal_tracker.settings

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Make entrypoint executable
RUN chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Entrypoint handles migrations, collectstatic, and server start
ENTRYPOINT ["/entrypoint.sh"]
