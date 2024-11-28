import os
import json
from io import BytesIO
import requests
from minio import Minio
from minio.error import S3Error
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from flask import Flask, request, jsonify
from fastapi import FastAPI, UploadFile, File, HTTPException
from controllers.challenge import extract_requirements_and_skills_with_json, generate_questions_from_requirements,evaluate_candidate_responses,match_offer_application
 
app = Flask(__name__)
 
# Load model and tokenizer
model_name = "meta-llama/Llama-3.2-3B-Instruct"
hf_token = os.getenv("HUGGINGFACE_TOKEN")
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=hf_token)
model = AutoModelForCausalLM.from_pretrained(model_name, use_auth_token=hf_token, torch_dtype=torch.float16)
model.to("cuda")

# MinIO Configuration
minio_address = os.getenv("MINIO_ADDRESS", "localhost:9000")
minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
minio_client = Minio(minio_address, access_key=minio_access_key, secret_key=minio_secret_key, secure=False)

async def upload_file(bucket: str, id: int, name:str, response):       
    # Upload the file to MinIO
    json_bytes = BytesIO(response.encode("utf-8"))
    object_path = f"{id}/" + name
    minio_client.put_object(bucket_name=bucket, 
                            object_name=object_path,            
                            data=json_bytes,            
                            length=len(response),            
                            content_type="application/json"        
                            ) 
    return

def download_file(bucket: str, object_name: str):
    """
    Downloads a file from the specified bucket in MinIO.

    :param bucket: The name of the bucket
    :param object_name: The path to the file within the bucket
    :return: The contents of the file as a string
    """
    try:
        # Get the object from the specified bucket
        response = minio_client.get_object(bucket_name=bucket, object_name=object_name)

        # Read the content from the response and decode it
        file_content = response.read().decode("utf-8")

        # Close the response stream
        response.close()
        response.release_conn()

        return file_content

    except Exception as e:
        print(f"An error occurred while downloading the file: {e}")
        return None
 
def format_messages(messages):
    """
    Formats messages for the model.
    """
    formatted = ""
    for message in messages:
        role = message["role"]
        content = message["content"]
        if role == "system":
            formatted += f"[SYSTEM]\n{content}\n"
        elif role == "user":
            formatted += f"[USER]\n{content}\n"
        elif role == "assistant":
            formatted += f"[ASSISTANT]\n{content}\n"
    # Add the assistant prompt to direct response
    formatted += "[ASSISTANT]\n"
    return formatted
 
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    messages = data.get("messages", [])
    # Format messages for the model
    input_text = format_messages(messages)
    inputs = tokenizer(input_text, return_tensors="pt").to("cuda")
    # Generate response
    outputs = model.generate(
        **inputs,
        max_length=2024,
        do_sample=True,
        temperature=0.7,
        eos_token_id=tokenizer.convert_tokens_to_ids("\n[USER]")  # Stop when a new user input begins
    )
    response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract only the assistant's response
    assistant_start = response_text.find("[ASSISTANT]") + len("[ASSISTANT]\n")
    user_start = response_text.find("\n[USER]", assistant_start)
    if user_start != -1:
        response_text = response_text[assistant_start:user_start].strip()
    else:
        response_text = response_text[assistant_start:].strip()
 
    return jsonify({"response": response_text})

@app.route("/generate_challenge", methods=["POST"])
def challenge():
    try:
        # Extract the data from the JSON payload
        data = request.get_json()
        if not data:
            raise ValueError("No JSON payload found in the request.")

        question_count = 10 #data.get("question_count")
        job_level = 'senior' #data.get("job_level")

        # Validate required fields
        if not data or not question_count or not job_level:
            raise ValueError("Missing required fields: 'json', 'question_count', or 'job_level'.")

        # Process the input (call your functions)
        requirements_json = extract_requirements_and_skills_with_json(data)

        questions_json = generate_questions_from_requirements(requirements_json, question_count, job_level)
        print("Generated Questions:", questions_json)
        upload_file('jobs', data.get('job_id'), 'challenge.json', questions_json)
        #return jsonify(requirements_json)
        return jsonify([requirements_json, questions_json])

    except Exception as e:
        print(f"Error occurred: {e}")  # Log the error
        return jsonify({"error": str(e)}), 500

@app.route("/generate_evaluation", methods=["POST"])
def evaluation():
    try:    
        # Extract the data from the JSON payload
        data = request.get_json()
        if not data:
            raise ValueError("No JSON payload found in the request.")

        # Bewertungen erstellen
        result = evaluate_candidate_responses(data)
        upload_file('applicants', data.get('applicant_id'), 'ChallengeSolution.json', result)
        return jsonify(result)

    except Exception as e:
        print(f"Error occurred: {e}") # Log the error
        return jsonify({"error": str(e)}), 500

@app.route("/assess_job", methods=["POST"])
def assess_job():
    try:
        # Extract the data from the JSON payload
        data = request.get_json()
        if not data:
            raise ValueError("No JSON payload found in the request.")

        # Validate required fields
        if not data.get('text'):
            raise ValueError("Missing required fields: 'text")

        # Process the input (call your functions)
        requirements_json = extract_requirements_and_skills_with_json(data)
        upload_file('jobs', data.get('job_id'), 'anforderung.json', requirements_json)
        return jsonify([requirements_json])

    except Exception as e:
        print(f"Error occurred: {e}")  # Log the error
        return jsonify({"error": str(e)}), 500


@app.route("/assess_applicant/<int:applicant_id>/<int:job_id>", methods=["POST"])
def assess_applicant(applicant_id: int, job_id: int):
    
    cv = download_file(bucket='applicants', object_name=f"{applicant_id}/" + 'cv.json')
    job_description = download_file(bucket='jobs', object_name=f"{job_id}/" + 'job_description.json')
    resume = cv.get('text')
    job_posting = job_description.get('text')

    try:    
        result = match_offer_application(job_posting, resume)
        upload_file(bucket='applicants', id=applicant_id, name='applicant_eval.json', response=result)

    except Exception as e:
        print(f"Error occurred: {e}")  # Log the error
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
