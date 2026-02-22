FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Run the application
# Railway provides PORT env var, fallback to 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
