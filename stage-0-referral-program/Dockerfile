# Use official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /app

# Copy dependency specifications
COPY requirements.txt .

# Install dependencies without cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/

# Default entrypoint runs the main ETL pipeline and exports report to /app/output
# When running with `-v $(pwd)/output:/app/output`, the report is saved directly on the host machine.
ENTRYPOINT ["python", "src/pipeline.py"]
CMD ["--data-dir", "/app/data", "--output-dir", "/app/output"]
