FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p .chroma_store

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROMA_PERSIST_DIR=/app/.chroma_store

# Build the knowledge index
RUN python -m app.ingest.build_index

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
