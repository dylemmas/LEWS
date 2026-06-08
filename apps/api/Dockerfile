FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps for asyncpg + argon2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libssl-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install . && pip install "uvicorn[standard]" gunicorn

COPY app ./app

# Train model on first build (cache bust on train.py changes)
COPY app/ml/train.py ./app/ml/train.py
RUN if [ ! -f app/ml/model_v1.joblib ]; then python -m app.ml.train || true; fi

EXPOSE 8000

CMD ["uvicorn", "app.main:application", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
