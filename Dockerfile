# Use official slim Python image
FROM python:3-slim

# Expose the port your app will run on
EXPOSE 8000

# Keeps Python from generating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier logging
ENV PYTHONUNBUFFERED=1

# Set work directory first
WORKDIR /app

# Copy requirements first (to leverage Docker cache)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Create a non-root user and give permissions
RUN adduser --disabled-password --gecos "" --uid 5678 appuser \
    && chown -R appuser /app
USER appuser

# Start app with gunicorn
# Change 'app:app' to your actual module and app object
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

