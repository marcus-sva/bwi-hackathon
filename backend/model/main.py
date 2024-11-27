import os
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from flask import Flask, request, jsonify
from controllers.challenge import extract_requirements_and_skills_with_db, generate_questions_from_requirements
 
app = Flask(__name__)
 
# Load model and tokenizer
model_name = "meta-llama/Llama-3.1-8B-Instruct"
hf_token = os.getenv("HUGGINGFACE_TOKEN")
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=hf_token)
model = AutoModelForCausalLM.from_pretrained(model_name, use_auth_token=hf_token, torch_dtype=torch.float16)
model.to("cuda")
 
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
        max_length=512,
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
def challenge(json(job_text,job_title), question_count, job_level):

    requirements_json = extract_requirements_and_skills_with_db(job_posting, job_title)
    questions_json = generate_questions_from_requirements(requirements_json, question_count=10, job_level="Junior")
    #request2minio challenge_json,   
    print(questions_json)
    return questions_json

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)