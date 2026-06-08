FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /sim

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .

COPY . .

CMD ["python", "app.py"]
