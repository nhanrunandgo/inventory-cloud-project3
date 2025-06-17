# Guide to run
# On: docker compose up -d
# Off: docker compose down

# Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR .

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask app
COPY . .

# Expose the port used by Gunicorn
EXPOSE 5000

# Run the app with Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
