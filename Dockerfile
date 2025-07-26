# Use Python 3.9 slim as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file from root directory
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories for uploads and outputs
RUN mkdir -p /app/uploads /app/data

# Copy the source code
COPY src/ /app/src/

# Set working directory to src
WORKDIR /app/src

# Expose port 8000
EXPOSE 8000

# Command to run the application from new structure
CMD ["python", "-m", "uvicorn", "financial_analysis.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
