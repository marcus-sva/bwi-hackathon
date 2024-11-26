FROM python:3.10-alpine
 
# Install system dependencies
RUN apk update && \
    apk upgrade --no-cache && \
    rm -rf /var/cache/apk/*
 
# Set the working directory
WORKDIR /app
 
# Copy the application code
COPY . .
 
# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
 
# Expose the port
EXPOSE 8000
 
# Command to run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]