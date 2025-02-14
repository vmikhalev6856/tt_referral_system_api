FROM python:3.13
WORKDIR /app
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock ./
RUN poetry env use python
RUN poetry install --no-root --no-interaction --no-ansi
COPY . .
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
