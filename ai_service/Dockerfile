FROM python:3.11

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8001

# Run the application (cloud databases - no waiting needed)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
