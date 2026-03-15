# Use a modern Python base image
FROM python:3.11-slim

# Install system dependencies needed for RDKit, ChromaDB, and AWS CLI
RUN apt-get update && apt-get install -y \
    build-essential \
    libxrender1 \
    libxext6 \
    libsm6 \
    libfontconfig1 \
    libfreetype6-dev \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI (needed for S3-to-EFS bootstrap)
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip ./aws

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the SentenceTransformer model to speed up startup
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
COPY app.py .

# Create a directory for the local ChromaDB (to be overridden by EFS mount in AWS)
RUN mkdir -p /app/chroma_db

# Set environment variables
ENV CHROMA_PATH=/app/chroma_db
ENV HOST=0.0.0.0
ENV PORT=8000

# Expose the API port
EXPOSE 8000

# Start the FastAPI app using Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
