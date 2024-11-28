import io
import json
import os
import random
import shutil
import tempfile
from io import BytesIO

from PyPDF2 import PdfReader
from fastapi import FastAPI, UploadFile, File, HTTPException
from minio import Minio
from minio.error import S3Error
from pydantic import BaseModel

minio_address = os.getenv("MINIO_ADDRESS", "localhost:9000")
minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
minio_client = Minio(minio_address, access_key=minio_access_key, secret_key=minio_secret_key, secure=False)
app = FastAPI()


def random_id():
    return random.randint(1, 1000)


def write_file_to_tempfile(file: UploadFile) -> str:
    """
    Writes an UploadFile to a temporary file without deleting it afterward.

    Args:
        file (UploadFile): The uploaded file to save.

    Returns:
        str: The path to the temporary file.
    """
    # Create a named temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_filename = temp_file.name  # Save the path for later use

    try:
        # Reset file pointer to the start
        file.file.seek(0)

        # Write the uploaded file to the temporary file
        with open(temp_filename, "wb") as f:
            shutil.copyfileobj(file.file, f)

        return temp_filename
    finally:
        # Make sure to leave the UploadFile file open
        file.file.seek(0)


def pdf_to_json(pdf_filename: str) -> str:
    """
    Processes a PDF file and extracts its text content.

    This function reads the content of a PDF file, extracting text from all pages,
    and returns it as a single concatenated string. It is specifically designed
    to handle applicant and job data, enabling PDF-to-text processing.

    Args:
        pdf_filename (str):
            The path to the PDF file to process.

    Returns:
        str:
            The extracted text content from the PDF, concatenated from all pages.
    """
    reader = PdfReader(pdf_filename)
    content = ""
    for page in reader.pages:
        content += page.extract_text()

    return content


@app.post("/cv/{job_id}/pdf")
async def upload_cv(job_id: int, file: UploadFile = File(...)):
    """
    Endpoint to upload a PDF as 'cv.pdf' to MinIO under the path applicants/RANDOM_APPLICANT_ID/cv.pdf.
    The PDF file will be converted to json and uploaded to applicants/RANDOM_APPLICANT_ID/cv.json.
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

        # Write PDF to temporary file, convert it and delete the temporary file
        pdf_filename = None
        try:
            pdf_filename = write_file_to_tempfile(file)
            print(f"Wrote PDF to TempFile {pdf_filename}")

            pdf_content = pdf_to_json(pdf_filename)
        finally:
            if 'pdf_filename' in locals() and os.path.exists(pdf_filename):
                os.remove(pdf_filename)
                print(f"TempFile {pdf_filename} removed successfully.")

        pdf_dict = {
            "job_id": job_id,
            "file": "cv.pdf",
            "text": pdf_content
        }
        pdf_json = json.dumps(pdf_dict)

        # Upload the file to MinIO
        json_bytes = BytesIO(pdf_json.encode("utf-8"))
        object_path = f"{random_applicants_id}/cv.json"

        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=object_path,
            data=json_bytes,
            length=len(pdf_json),
            content_type="application/json"
        )

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

        # Write PDF to temporary file, convert it and delete the temporary file
        pdf_filename = None
        try:
            pdf_filename = write_file_to_tempfile(file)
            print(f"Wrote PDF to TempFile {pdf_filename}")

            pdf_content = pdf_to_json(pdf_filename)
            # quick and dirty for scrum master position
            pdf_content = pdf_content.replace("Jetzt online bewerben\nJetzt online bewerben", "", 1)
            # extract the job title
            title = pdf_content.split(" \n", 1)[0]
        finally:
            if 'pdf_filename' in locals() and os.path.exists(pdf_filename):
                os.remove(pdf_filename)
                print(f"TempFile {pdf_filename} removed successfully.")

        pdf_dict = {
            "job_id": job_id,
            "file": "job_description.json",
            "title": title,
            "text": pdf_content
        }
        pdf_json = json.dumps(pdf_dict)

        # Upload the file to MinIO
        json_bytes = BytesIO(pdf_json.encode("utf-8"))
        object_path = f"{job_id}/job_description.json"

        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=object_path,
            data=json_bytes,
            length=len(pdf_json),
            content_type="application/json"
        )

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
