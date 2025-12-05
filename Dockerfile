FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=meal_tracker.settings \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Create an isolated virtualenv and upgrade pip
RUN python -m venv "$VIRTUAL_ENV" \
    && "$VIRTUAL_ENV/bin/pip" install --upgrade pip

# Install dependencies into the venv
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copy application code
COPY . /app/

# Create a non-root user and fix permissions
RUN addgroup --system app && adduser --system --ingroup app app \
    && chmod +x /app/entrypoint.sh \
    && chown -R app:app /app

USER app

# Expose port
EXPOSE 8000

# Entrypoint handles migrations, collectstatic, and server start
ENTRYPOINT ["/app/entrypoint.sh"]
