# Use an official Python 3.11 slim image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pinned+hashed lockfile and install dependencies
# regen: uv pip compile requirements.txt --generate-hashes -o requirements.lock --python-version 3.11
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

# Pre-download Silero VAD model to avoid downloading at runtime
RUN python -c "from livekit.plugins import silero; silero.VAD.load()"

# Copy the rest of the application code
COPY . .

# Expose the Token API port
EXPOSE 8080

# Command to run both the API server and the LiveKit worker
CMD ["python", "main.py"]
