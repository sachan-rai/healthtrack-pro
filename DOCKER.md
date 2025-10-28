# HealthTrack Pro - Docker Setup

## Build and Run with Docker

### Build the image
```bash
docker build -t healthtrack-pro .
```

### Run the container
```bash
docker run -p 8000:8000 -e OPENAI_API_KEY=your_api_key_here healthtrack-pro
```

### Using Docker Compose
```bash
# Create docker-compose.yml
version: '3.8'
services:
  healthtrack-pro:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./app/data:/app/app/data
      - ./.chroma_store:/app/.chroma_store
```

Then run:
```bash
docker-compose up --build
```
