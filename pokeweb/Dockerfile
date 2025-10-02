# Use a lightweight Python base
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies you might need (SQLite, build tools, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy your requirements file first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code (everything in src/) into the container
COPY src/ .

# Expose Flask’s default port
EXPOSE 5000

# Run Flask
CMD ["python", "app.py"]
