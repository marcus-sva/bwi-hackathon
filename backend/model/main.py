import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from controllers.challenge import extract_requirements_and_skills_with_json, generate_questions_from_requirements

# Initialize FastAPI
app = FastAPI()

# Load model and tokenizer
model_name = "meta-llama/Llama-3.2-3B-Instruct"
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


# Request schema for /generate endpoint
class GenerateRequest(BaseModel):
    messages: list


@app.post("/generate")
async def generate(request: GenerateRequest):
    """
    Generate a response from the model.
    """
    try:
        # Format messages for the model
        input_text = format_messages(request.messages)
        inputs = tokenizer(input_text, return_tensors="pt").to("cuda")
        # Generate response
        outputs = model.generate(
            **inputs,
            max_length=1024,
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

        return {"response": response_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Request schema for /generate_challenge endpoint
class ChallengeRequest(BaseModel):
    job_posting_json: dict
    question_count: int
    job_level: str


@app.post("/generate_challenge")
async def challenge(request: ChallengeRequest):
    """
    Generate interview questions based on job posting and requirements.
    """
    try:
        # Extract data from the request
        job_posting_json = request.job_posting_json
        question_count = request.question_count
        job_level = request.job_level

        # Validate required fields (this is optional since Pydantic handles validation)
        if not job_posting_json or not question_count or not job_level:
            raise ValueError("Missing required fields: 'job_posting_json', 'question_count', or 'job_level'.")

        # Process the input
        requirements_json = extract_requirements_and_skills_with_json(job_posting_json)
        questions_json = generate_questions_from_requirements(requirements_json, question_count, job_level)

        return questions_json

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
