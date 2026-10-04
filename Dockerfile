FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CLIMATE_ENV=production

WORKDIR /app
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY app.py gunicorn.conf.py ./
COPY climate/ climate/
COPY sql/ sql/
COPY templates/ templates/
COPY static/ static/

RUN useradd --system --uid 10001 --home-dir /nonexistent climate \
    && chown -R climate:climate /app
USER 10001:10001

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
