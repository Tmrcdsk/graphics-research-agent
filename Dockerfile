ARG PYTHON_IMAGE=python:3.11-slim
FROM ${PYTHON_IMAGE}

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY app ./app
COPY tests ./tests
COPY docs ./docs

RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -e ".[dev]"

CMD ["python", "-m", "app.main", "serve"]
