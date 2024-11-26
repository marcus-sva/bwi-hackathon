FROM python:3.10-slim
 
# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake libsm6 libxext6 libxrender-dev libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*
 
# Set the working directory
WORKDIR /app
 
# Copy the requirements file
COPY app/requirements.txt .
 
# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
 
# Copy the application code
COPY app/ .
 
# Expose the port
EXPOSE 8000
 
# Command to run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]