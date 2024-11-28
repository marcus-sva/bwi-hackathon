### start entire application
docker-compose -f compose.yaml up --build

### frontend + minio only
docker-compose -f compose.yaml up --build frontend application-minio

### coordinator and minio only
docker-compose -f compose.yaml up --build backend-coordinator application-minio

### minio only
docker-compose -f compose.yaml up --build application-minio

### docker configerror
docker system prune --all --volumes