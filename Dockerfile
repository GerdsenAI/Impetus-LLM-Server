# Note: This Dockerfile is experimental and not officially supported in v0.1.0
# Impetus is optimized for native macOS on Apple Silicon
# Docker support is planned for future releases

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy backend files
COPY gerdsen_ai_server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY gerdsen_ai_server/ ./gerdsen_ai_server/
COPY setup.py pyproject.toml MANIFEST.in ./

# Install the package
RUN pip install -e .

# Create directories
RUN mkdir -p /root/.impetus/models /root/.impetus/cache /root/.impetus/logs

# Expose ports
EXPOSE 8080
EXPOSE 5173

# Set environment variables
ENV IMPETUS_HOST=0.0.0.0
ENV IMPETUS_PORT=8080
ENV PYTHONUNBUFFERED=1

# Note: MLX requires Apple Silicon and won't work in Docker
# This container can only run in API proxy mode or with CPU inference

CMD ["python", "gerdsen_ai_server/src/main.py"]