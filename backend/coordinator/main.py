import asyncio
import io
import json
import os
import random
import tempfile
import copy

from fastapi import FastAPI, UploadFile, File, HTTPException
from minio import Minio
from minio.error import S3Error
from pydantic import BaseModel
from tika import parser

minio_address = os.getenv("MINIO_ADDRESS", "localhost:9000")
minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
minio_client = Minio(minio_address, access_key=minio_access_key, secret_key=minio_secret_key, secure=False)
app = FastAPI()


def random_id():
    return random.randint(1, 1000)

async def cv_pdf_to_json(applicant_id: int, job_id: int, file: UploadFile):
    """
    Converts a CV PDF to JSON and uploads it to MinIO under the proper path.

    Args:
        applicant_id (str): The unique ID of the applicant.
        job_id (int): The job ID.
        file (UploadFile): The uploaded PDF file.
    """
    bucket_name = "applicants"
    json_object_path = f"{applicant_id}/{job_id}/cv.json"

    # Temporary file management
    temp_file = None
    try:
        # Write the uploaded PDF to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        # Call the parser with the temporary file handle (replace with actual parser logic)
        parsed_data = await parse_document(temp_file_path)

        # Write parsed data to a temporary JSON file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_json_file:
            temp_json_file.write(parsed_data.encode("utf-8"))
            temp_json_path = temp_json_file.name

        # Ensure the bucket exists in MinIO
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        # Upload the JSON file to MinIO
        with open(temp_json_path, "rb") as json_file:
            minio_client.put_object(
                bucket_name,
                json_object_path,
                json_file,
                os.path.getsize(temp_json_path),
                content_type="application/json",
            )

    except Exception as e:
        raise Exception(f"An error occurred during PDF to JSON conversion: {str(e)}")
    finally:
        # Clean up temporary files
        if temp_file and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if 'temp_json_path' in locals() and os.path.exists(temp_json_path):
            os.remove(temp_json_path)

    print(f"CV JSON successfully uploaded to MinIO: {bucket_name}/{json_object_path}")

async def parse_document(pdf_filename):
    """
    gets text from document
    """
    raw = parser.from_file(pdf_filename)
    metadata = raw['metadata']
    # pprint(metadata)
    content = raw['content']

    doc_dict = {
        "file": pdf_filename,
        "text": content
    }
    doc_json = json.dumps(doc_dict)
    return doc_json


@app.post("/cv/{job_id}/pdf")
async def upload_cv(job_id: int, file: UploadFile = File(...)):
    """
    Endpoint to upload a PDF as 'cv.pdf' to MinIO under the path applicants/RANDOM_APPLICANT_ID/cv.pdf.
    """
    try:
        # Ensure the uploaded file is a PDF
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

        # Validate job_id
        if job_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid job_id. It must be a positive integer.")

        # Generate a random applicants_id
        random_applicants_id = random_id()

        # Define bucket name and object path
        bucket_name = "applicants"
        object_path = f"{random_applicants_id}/cv.pdf"

        # Ensure the bucket exists; create it if not
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        # Upload the PDF to MinIO
        minio_client.put_object(
            bucket_name,
            object_path,
            file.file,  # File-like object
            length=-1,  # Let MinIO calculate the file size
            part_size=10 * 1024 * 1024,  # Part size for multipart uploads (10MB)
            content_type="application/pdf",  # Set content type to PDF
        )

        # @TODO TRIGGER pdf to json generation via other service
        asyncio.create_task(cv_pdf_to_json(random_applicants_id, job_id))

        # Return success response
        return {
            "message": f"File uploaded successfully.",
            "path": f"{bucket_name}/{object_path}",
            "applicant_id": f"{random_applicants_id}",
        }

    except HTTPException as e:
        # Re-raise any HTTP exceptions to return the correct status code
        raise e
    except S3Error as e:
        # Catch any other S3 errors and return a 500 error
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        # Catch any other unexpected errors and return a 500 error
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.get("/challenge/{applicant_id}")
async def get_challenge(applicant_id: str):
    """
    Retrieves the challenge.json file for a specific applicant.
    Searches for challenge.json in applicants/$APPLICANT_ID/$JOB_ID/challenge.json.
    """
    bucket_name = "applicants"

    try:
        # Check if the bucket exists
        if not minio_client.bucket_exists(bucket_name):
            raise HTTPException(status_code=404, detail="Bucket does not exist.")

        # List all objects under the applicant_id directory
        objects = minio_client.list_objects(bucket_name, prefix=f"{applicant_id}/", recursive=True)

        # Find the path to challenge.json
        challenge_path = None
        for obj in objects:
            if obj.object_name.endswith("challenge.json"):
                challenge_path = obj.object_name
                break

        # If challenge.json is not found
        if not challenge_path:
            raise HTTPException(status_code=404, detail="challenge.json not found for the given applicant_id.")

        # Retrieve challenge.json
        try:
            response = minio_client.get_object(bucket_name, challenge_path)

            # Read and decode the file content
            content = response.read().decode("utf-8")

            # Return the JSON content
            return json.loads(content)
        finally:
            response.close()
            response.release_conn()

    except HTTPException as e:
        # Re-raise any HTTP exceptions to return the correct status code
        raise e
    except S3Error as e:
        # Catch any other S3 errors and return a 500 error
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        # Catch any other unexpected errors and return a 500 error
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# Pydantic model to validate incoming JSON payload
class ChallengeSolution(BaseModel):
    applicant_id: int
    job_id: int
    solution: str


@app.put("/challenge_solution/{applicant_id}/{job_id}")
async def upload_challenge_solution(applicant_id: int, job_id: int, challenge_solution: ChallengeSolution):
    """
    Uploads challenge_solution.json to the path:
    applications/{applicant_id}/{job_id}/challenge_solution.json
    """
    # Verify if the applicant_id and job_id in the body match the URL parameters
    if challenge_solution.applicant_id != applicant_id:
        raise HTTPException(status_code=400, detail="Applicant ID in the URL does not match the body.")

    if challenge_solution.job_id != job_id:
        raise HTTPException(status_code=400, detail="Job ID in the URL does not match the body.")

    # Construct the object path in MinIO
    bucket_name = "applicants"
    object_path = f"{applicant_id}/{job_id}/challenge_solution.json"

    try:
        # Ensure the bucket exists, create it if not
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        # Convert the Python object to JSON
        file_content = challenge_solution.model_dump_json().encode('utf-8')  # Convert to bytes
        file_like_object = io.BytesIO(file_content)  # Wrap bytes in a BytesIO object

        # Upload the JSON file to MinIO
        minio_client.put_object(
            bucket_name,
            object_path,
            data=file_like_object,  # File content in bytes
            length=len(file_content),  # Size of the content in bytes
            content_type="application/json"  # Content type is JSON
        )

        # Return a success message
        return {
            "message": "challenge_solution.json uploaded successfully.",
            "path": f"{bucket_name}/{object_path}",
            "applicant_id": applicant_id,
            "challenge_id": job_id,
        }

    except HTTPException as e:
        # Re-raise any HTTP exceptions to return the correct status code
        raise e
    except S3Error as e:
        # Catch any other S3 errors and return a 500 error
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        # Catch any other unexpected errors and return a 500 error
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.post("/job/{job_id}/pdf")
async def upload_job_description(job_id: int, file: UploadFile = File(...)):
    """
    Endpoint to upload a PDF as 'job_description.pdf' to MinIO under the path jobs/{JOB_ID}/job_description.pdf.
    """
    try:
        # Ensure the uploaded file is a PDF
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

        # Validate job_id
        if job_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid job_id. It must be a positive integer.")

        # Define bucket name and object path
        bucket_name = "jobs"
        object_path = f"{job_id}/job_description.pdf"

        # Ensure the bucket exists; create it if not
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        # Upload the PDF to MinIO
        minio_client.put_object(
            bucket_name,
            object_path,
            file.file,  # File-like object
            length=-1,  # Let MinIO calculate the file size
            part_size=10 * 1024 * 1024,  # Part size for multipart uploads (10MB)
            content_type="application/pdf",  # Set content type to PDF
        )

        await cv_pdf_to_json("1", job_id, file)

        # Return success response
        return {
            "message": f"File uploaded successfully.",
            "path": f"{bucket_name}/{object_path}",
            "job_id": f"{job_id}",
        }

    except HTTPException as e:
        # Re-raise any HTTP exceptions to return the correct status code
        raise e
    except S3Error as e:
        # Catch any other S3 errors and return a 500 error
        raise HTTPException(status_code=500, detail=f"MinIO error: {str(e)}")
    except Exception as e:
        # Catch any other unexpected errors and return a 500 error
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")