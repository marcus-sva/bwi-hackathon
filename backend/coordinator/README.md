FastAPI backend to coordinate between minio and model backend.


local image
docker build -t coordinator -f Dockerfile .
docker run -p 8000:8000 coordinator
