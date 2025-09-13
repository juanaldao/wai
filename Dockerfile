# Use Python base image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app.py .

# Run with Gunicorn (prod server)
CMD exec gunicorn --bind :8080 --workers 2 --threads 8 --timeout 0 app:app
