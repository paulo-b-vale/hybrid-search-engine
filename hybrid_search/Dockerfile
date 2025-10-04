FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set up NLTK data directories and permissions
RUN mkdir -p /home/appuser/nltk_data && \
    mkdir -p /usr/local/nltk_data && \
    mkdir -p /usr/local/lib/python3.11/site-packages/llama_index/core/_static/nltk_cache && \
    chmod 755 /usr/local/lib/python3.11/site-packages/llama_index/core/_static && \
    chmod 755 /usr/local/lib/python3.11/site-packages/llama_index/core/_static/nltk_cache

# Download all required NLTK data
RUN python -c "import nltk; \
    nltk.download('punkt', download_dir='/usr/local/nltk_data'); \
    nltk.download('punkt_tab', download_dir='/usr/local/nltk_data'); \
    nltk.download('stopwords', download_dir='/usr/local/nltk_data'); \
    nltk.download('averaged_perceptron_tagger', download_dir='/usr/local/nltk_data')"

# Make NLTK data accessible to all users
RUN chmod -R 755 /usr/local/nltk_data

# Copy application code
COPY . .

# Set ownership of app files to appuser
RUN chown -R appuser:appuser /app

# Set environment variables
ENV NLTK_DATA=/usr/local/nltk_data:/home/appuser/nltk_data
ENV PYTHONPATH=/app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "server.py"]