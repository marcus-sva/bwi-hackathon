import os
import json
from io import BytesIO
from minio import Minio
from minio.error import S3Error
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from flask import Flask, request, jsonify
from fastapi import FastAPI, UploadFile, File, HTTPException
from controllers.challenge import extract_requirements_and_skills_with_json, generate_questions_from_requirements,evaluate_candidate_responses
 
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

        job_posting_json = data.get("job_posting_json")
        question_count = 10 #data.get("question_count")
        job_level = 'senior' #data.get("job_level")
        #print(job_posting_json)
        # Validate required fields
        if not job_posting_json or not question_count or not job_level:
            raise ValueError("Missing required fields: 'job_posting_json', 'question_count', or 'job_level'.")

        # Process the input (call your functions)
        requirements_json = extract_requirements_and_skills_with_json(data)
        #print("Requirements JSON:", jsonify(requirements_json))

        questions_json = generate_questions_from_requirements(requirements_json, question_count, job_level)
        #print("Generated Questions:", questions_json)
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
        return jsonify(result)

    except Exception as e:
        print(f"Error occurred: {e}") # Log the error
        return jsonify({"error": str(e)}), 500

@app.route("/assess_job", methods=["POST"])
def assess_job():
    pass


@app.route("/assess_applicant", methods=["POST"])
def assess_job():
    pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
