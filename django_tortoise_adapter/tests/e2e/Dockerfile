# Use a correct python image
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install uv and curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install uv

# 2. Copy polls pyproject.toml
COPY pyproject.toml .

# Install dependencies from pyproject.toml globally
RUN uv pip install --system -e .

# 4. Copy the project code
COPY . .

# adapter_source will be mounted via docker-compose
ENV PYTHONPATH=/app:/app/adapter_source

# Expose port
EXPOSE 8000

# Run uvicorn
CMD ["uvicorn", "polls_project.asgi:application", "--host", "0.0.0.0", "--port", "8000"]

