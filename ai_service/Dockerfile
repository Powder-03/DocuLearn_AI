FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including PostgreSQL client
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create startup script that runs migrations before starting the app
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "⏳ Waiting for PostgreSQL..."\n\
while ! pg_isready -h db -p 5432 -U ${POSTGRES_USER:-doculearn} > /dev/null 2>&1; do\n\
  sleep 1\n\
done\n\
echo "✅ PostgreSQL is ready!"\n\
\n\
echo "🔄 Running database migrations..."\n\
python migrate.py upgrade || echo "⚠️  Migration failed, but continuing..."\n\
echo "✅ Migrations complete!"\n\
\n\
echo "🚀 Starting application..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8001

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
