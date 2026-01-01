FROM python:3.12-slim

# Set working directory to parent of mvp
WORKDIR /app

# Install uv for fast dependency installation
RUN pip install uv

# Copy the entire mvp directory
COPY . ./mvp/

# Change to mvp directory for uv sync
WORKDIR /app/mvp

# Install dependencies
RUN uv sync --frozen --no-dev

# Set Python path to /app so 'mvp.app...' imports work
ENV PYTHONPATH=/app

# Default command (can be overridden)
CMD ["uv", "run", "uvicorn", "mvp.main:app", "--host", "0.0.0.0", "--port", "8000"]
