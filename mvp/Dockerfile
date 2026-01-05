FROM python:3.12-slim

# Set working directory to parent of mvp
WORKDIR /app

# Install uv for fast dependency installation
RUN pip install uv

# Copy the entire mvp directory
# Copy only dependency files first to leverage Docker cache
COPY pyproject.toml uv.lock ./mvp/

# Change to mvp directory
WORKDIR /app/mvp

# Install dependencies (This layer will be cached unless lockfile changes)
RUN uv sync --frozen --no-dev

# Copy the rest of the application
COPY . /app/mvp/

# Set Python path to /app so 'mvp.app...' imports work
ENV PYTHONPATH=/app

# Default command (can be overridden)
CMD ["uv", "run", "uvicorn", "mvp.main:app", "--host", "0.0.0.0", "--port", "8000"]
