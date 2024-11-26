from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from flask import Flask, request, jsonify
 
app = Flask(__name__)
 
# Modell und Tokenizer laden
model_name = "meta-llama/Llama-3.2-3B-Instruct"
hf_token = os.getenv("HUGGINGFACE_TOKEN")
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16)
model.to("cuda")
 
def format_messages(messages):
    """
    Formatiert Nachrichten für das Modell.
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
    return formatted
 
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    messages = data.get("messages", [])
    # Nachrichten für das Modell formatieren
    input_text = format_messages(messages)
    inputs = tokenizer(input_text, return_tensors="pt").to("cuda")
    # Antwort generieren
    outputs = model.generate(**inputs, max_length=512, do_sample=True, temperature=0.7)
    response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
 
    return jsonify({"response": response_text})
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)