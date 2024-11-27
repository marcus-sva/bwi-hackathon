FastAPI backend to coordinate between minio and model backend.

## Docker

local image
docker build -t coordinator -f Dockerfile .
docker run -p 8000:8000 coordinator

## Rest Calls

### POST /cv

Upload a CV as a PDF file and store it in MinIO under the path `applicants/{RANDOM_APPLICANT_ID}/cv.pdf`.

```shell
curl -X POST "http://127.0.0.1:8000/cv" -F "file=@my-cv.pdf"
```

### GET /challenge/{applicant_id}

Retrieve the `challenge.json` file content for a specific applicant.

```shell
 curl -X GET http://127.0.0.1:8000/challenge/1
```

### PUT /challenge_solution/{applicant_id}/{job_id}

Upload the `challenge_solution.json` file to the path `applications/{applicant_id}/{job_id}/challenge_solution.json`.

```shell
curl -X PUT "http://127.0.0.1:8000/challenge_solution/1/1" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": 1,
    "job_id": 1,
    "solution": "This is my solution."
  }'
```

### POST /job

Upload a job description as a PDF file and store it in MinIO under the path `jobs/{RANDOM_JOB_ID}/job_description.pdf`.

```shell
curl -X POST "http://127.0.0.1:8000/job" -F "file=@developer-job-description.pdf"
```